"""Офлайн-інспекція збереженого куплету Борисова A68/A69. Див. quickstart.md."""
import argparse
import hashlib
import json
import os
from math import gcd
from pathlib import Path

import numpy as np
import pyworld
import soundfile as sf
from librosa import mel_frequencies
from librosa.filters import mel as mel_filter
from scipy import signal
from scipy.fft import rfft, rfftfreq

from common import ROOT, external_work_directory, protect_source_directories, read_csv


RATE, HOP, FFT, BANDS = 44100, 512, 2048, 128  # Seed-VC 44.1 kHz, full-v1
STEP = HOP / RATE
DB = 20 / np.log(10)
MARKERS = {"ˈ", "ˌ", "ː", " ", ",", ".", "^", "$"}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def require(test, message):
    if not test:
        raise ValueError(message)


def audio(path):
    x, rate = sf.read(path, dtype="float64")
    require(x.ndim == 1 and np.isfinite(x).all(), f"Expected finite mono WAV: {path}")
    return x, rate


def in_window(times, lo, hi):
    return (times >= lo) & (times < hi)


def quantiles(values):
    return np.percentile(values, [10, 50, 90]).tolist() if len(values) else None


def pitch(x, rate):
    d = gcd(rate, 16000)
    samples = signal.resample_poly(x, 16000 // d, rate // d)
    f0, times = pyworld.dio(samples, 16000, f0_floor=55, f0_ceil=650, frame_period=5)
    return times, pyworld.stonemask(samples, f0, times, 16000)


def amplitude_modulation(x, rate):
    power = signal.sosfiltfilt(signal.butter(4, 30, fs=rate, output="sos"), x*x)
    times = np.arange(0, len(x)/rate, .01)
    db = 10*np.log10(np.maximum(np.interp(times, np.arange(len(x))/rate, power), 1e-12))
    band = signal.butter(2, [3.5, 12], btype="bandpass", fs=100, output="sos")
    return times, signal.sosfiltfilt(band, db)


def waveform_mel(x):
    # Same reflect padding, periodic Hann, Slaney filters and natural log as modules/audio.py.
    padded = np.pad(x, (FFT-HOP)//2, mode="reflect")
    windows = np.lib.stride_tricks.sliding_window_view(padded, FFT)[::HOP]
    mag = np.sqrt(abs(rfft(windows * signal.windows.hann(FFT, sym=False)))**2 + 1e-9)
    basis = mel_filter(sr=RATE, n_fft=FFT, n_mels=BANDS, fmin=0, fmax=None)
    return np.log(np.maximum(basis @ mag.T, 1e-5))


def spectral_measures(logmel, centers, target):
    """Low harmonic comb contrast and broad spectral-envelope motion, on the same mel grid."""
    partials = []
    for k in range(1, 7):
        sample_hz = (k + np.array([-.5, 0, .5])) * target
        levels = np.array([np.interp(sample_hz, centers, frame) for frame in logmel.T])
        contrast = (levels[:, 1] - .5*(levels[:, 0]+levels[:, 2])) * DB
        partials.append(float(np.median(contrast)))
    envelopes = []
    for low, high in [(300, 1000), (1000, 2500)]:
        keep = in_window(centers, low, high)
        # A centroid on the mel grid is only a proxy for motion, not an F1/F2 estimate.
        magnitude = np.exp(logmel[keep])
        centroid = (centers[keep, None]*magnitude).sum(axis=0)/magnitude.sum(axis=0)
        envelopes.append(centroid)
    summary = {"harmonics_1_to_6_contrast_db": partials,
               "band_centroid_hz_p10_p50_p90": [quantiles(x) for x in envelopes]}
    return summary, envelopes


def nearby_peaks(x, rate, measured_f0):
    """Resolved companion peaks in the native waveform; AM and FM can also make sidebands."""
    nfft = 1 << (len(x)*4 - 1).bit_length()
    spectrum = abs(rfft(x * signal.windows.hann(len(x)), nfft))
    peaks = signal.find_peaks(spectrum)[0]
    hz = rfftfreq(nfft, 1/rate)[peaks]
    peaks_out = []
    min_spacing = max(3.5, 2*rate/len(x))  # Hann resolution; zero-padding adds no information.
    for k in range(1, 5):
        neighborhood = np.flatnonzero(abs(hz - k*measured_f0) < measured_f0*.45)
        if not len(neighborhood):
            peaks_out.append(None)
            continue
        main = neighborhood[np.argmax(spectrum[peaks[neighborhood]])]
        delta = hz - hz[main]
        others = neighborhood[(abs(delta[neighborhood]) >= min_spacing) &
                              (abs(delta[neighborhood]) <= 12)]
        levels = 20*np.log10(spectrum[peaks[others]]/spectrum[peaks[main]])
        peaks_out.append({"main_hz": float(hz[main]), "companions_hz_offset_dbc": [
            [float(delta[i]), float(level)] for i, level in zip(others, levels) if level >= -30]})
    return peaks_out


def vowel_audit(data, assembly, slots, native, dry):
    times = data["target_times"]
    generated = data["generated_mel"][0]
    reconstructed = waveform_mel(native)
    require(reconstructed.shape == generated.shape, "Mel and native waveform frame grids differ")
    centers = mel_frequencies(n_mels=BANDS+2, fmin=0, fmax=RATE/2)[1:-1]
    waves = {"native": native, "A68": dry}
    measurements = {key: (pitch(x, RATE), amplitude_modulation(x, RATE)) for key, x in waves.items()}
    results = {}
    for word, (lo, hi) in zip(("has", "heart"), assembly["postprocessing"]["windows_seconds"], strict=True):
        mask = in_window(times, lo, hi)
        slot_ids = np.unique(data["slot_ids"][mask])
        require(len(slot_ids) == 1 and slots[int(slot_ids[0])]["word"] == word, f"Window mismatch: {word}")
        score = data["score_f0"][mask]
        target = slots[int(slot_ids[0])]["note_hz"]
        row = {"target_window_s": [lo, hi], "note_hz": target,
               "score_zero_frames": int((score == 0).sum()), "frames": int(mask.sum())}
        semantic = data["semantic_features"][0, mask]
        row["identical_adjacent_semantic_pairs"] = int(np.all(np.diff(semantic, axis=0) == 0, axis=1).sum())
        for key, ((ft, f0), (at, am)) in measurements.items():
            samples = f0[in_window(ft, lo, hi)]
            voiced = samples[samples > 0]
            row[key] = {"voiced_fraction": float(len(voiced)/len(samples)),
                        "f0_hz_p10_p50_p90": quantiles(voiced),
                        "cents_vs_note_p10_p50_p90": quantiles(1200*np.log2(voiced/target)),
                        "am_3p5_12_hz_db_rms": float(np.sqrt(np.mean(am[in_window(at, lo, hi)]**2)))}
            if key == "native" and len(voiced):
                row["native_partial_peaks"] = nearby_peaks(native[round(lo*RATE):round(hi*RATE)],
                                                          RATE, np.median(voiced))
        row["generated_mel"], before = spectral_measures(generated[:, mask], centers, target)
        row["native_mel"], after = spectral_measures(reconstructed[:, mask], centers, target)
        row["band_centroid_generated_vs_native_r"] = [
            float(np.corrcoef(a, b)[0, 1]) if min(a.std(), b.std()) > 1e-9 else None
            for a, b in zip(before, after)]
        row["mel_difference_db_rms"] = float(np.sqrt(np.mean(((generated[:, mask]-reconstructed[:, mask])*DB)**2)))
        results[word] = row
    return results


def source_cues(x, rate):
    """Independent measurements on the spoken WAV, indexed in local source seconds."""
    width, step = round(.016*rate), round(.002*rate)
    padded = np.pad(x, (width//2, width//2), mode="reflect")
    windows = np.lib.stride_tricks.sliding_window_view(padded, width)[::step]
    window = signal.windows.hann(width, sym=False)
    magnitude = abs(rfft(windows*window))
    high = rfftfreq(width, 1/rate) >= 2000
    rms = np.sqrt(np.mean(windows**2, axis=1))
    hf = np.sqrt(2*(magnitude[:, high]**2).sum(axis=1)/(width*np.sum(window**2)))
    shape = magnitude/np.maximum(np.linalg.norm(magnitude, axis=1, keepdims=True), 1e-10)
    # Cosine distance over ~12 ms, centered on the time under examination.
    lag = round(.006*rate/step)
    sides = np.pad(shape, ((lag, lag), (0, 0)), mode="edge")
    change = 1-np.sum(sides[:-2*lag]*sides[2*lag:], axis=1)
    ft, f0 = pitch(x, rate)
    times = np.arange(len(windows))*step/rate
    nearest = np.searchsorted((ft[:-1]+ft[1:])/2, times)
    return {"t": times, "voiced": f0[nearest] > 0, "change": change,
            "rms_dbfs": 20*np.log10(np.maximum(rms, 1e-8)),
            "hf_dbfs": 20*np.log10(np.maximum(hf, 1e-8))}


def release_candidate(cues, phone_start, phone_end, mapped):
    # Inspect both sides of the label. Search for an active HF rise after closure.
    t, hf = cues["t"], cues["hf_dbfs"]
    scan = in_window(t, phone_start-.075, phone_end+.09)
    rise = hf - np.interp(t-.010, t, hf)
    peaks = signal.find_peaks(rise)[0]
    eligible = peaks[scan[peaks] & (hf[peaks] >= -60) & (rise[peaks] >= 6)]
    candidates = []
    for i in eligible:
        candidates.append({"source_s": float(t[i]), "hf_dbfs": float(hf[i]),
                           "rise_db_in_10ms": float(rise[i]),
                           "distance_to_nearest_mapped_center_ms": float(1000*min(abs(mapped-t[i]))),
                           "inside_p_label": bool(phone_start <= t[i] < phone_end)})
    return candidates


def acoustic_boundary(cues, boundary):
    """Strongest local spectral change near a label; its strength is recorded even in quiet regions."""
    t = cues["t"]
    nearby = np.flatnonzero(in_window(t, boundary-.020, boundary+.020))
    i = nearby[np.argmax(cues["change"][nearby])]
    return {"source_s": float(t[i]), "offset_ms": float((t[i]-boundary)*1000),
            "cosine_distance": float(cues["change"][i]), "rms_dbfs": float(cues["rms_dbfs"][i])}


def crop_control(slot, mapped, cues, line_duration):
    """Offline counterfactual: move only the two source nucleus anchors of the last slot."""
    vowel = next(p for p in slot["phones"] if p["label"] == "ɑ")
    lo, hi = vowel["source_s"]
    inset = .1*(hi-lo)
    candidate = [lo+inset, hi-inset]  # Interior of the approximate vowel label, subject to listening.
    start, end = slot["source_window_s"]
    end = min(end+.035, line_duration)  # full-v1 terminal release extension
    original = slot["effective_core_s"]
    alternate = np.interp(mapped, [start, *original, end], [start, *candidate, end])
    rows = {}
    for name, core, source_map in [("saved", original, mapped), ("candidate", candidate, alternate)]:
        samples = in_window(cues["t"], *core)
        rows[name] = {
            "source_core_s": core, "core_target_frames": int(in_window(source_map, *core).sum()),
            "frames_mapped_inside_vowel_label": int(in_window(source_map, lo, hi).sum()),
            "source_core_voiced_fraction": float(cues["voiced"][samples].mean()),
            "source_rms_dbfs_median": float(np.median(cues["rms_dbfs"][samples])),
            "source_hf_dbfs_median": float(np.median(cues["hf_dbfs"][samples])),
            "source_shape_change_median": float(np.median(cues["change"][samples]))}
    return rows


def audit_slots(data, generation, assembly, phones, source_audio):
    ids, times, mapped = (data[key] for key in ("slot_ids", "target_times", "mapped_source_seconds"))
    slots = generation["slots"]
    require([sum(s["line"] == line for s in slots) for line in range(1, 5)] == [10, 9, 10, 10],
            "Unexpected syllable counts")
    expected_ids = np.full(len(ids), -1)
    adjustments = {a["slot"]: a["new_vowel_window"] for a in assembly["h_boundary_adjustments"]}
    reports = []
    for index, slot in enumerate(slots):
        line = slot["line"]-1
        source = assembly["sources"][line]
        cues = source_audio[line]
        start, end = slot["start_seconds"], slot["end_seconds"]
        mask = in_window(times, start, end)
        require(mask.any() and (expected_ids[mask] == -1).all(), f"Missing/overlapping slot {index}")
        expected_ids[mask] = index
        local = mapped[mask] - source["source_offset"]
        require((np.diff(local) >= 0).all() and local[0] >= 0 and local[-1] <= source["duration"],
                f"Source-time map outside line or reversed in slot {index}")
        vs, ve = adjustments.get(index, slot["vowel_window"])
        core = in_window(local, vs, ve)
        observed = in_window(cues["t"], vs, ve)
        word = generation["text"][line].split()[slot["source_word_index"]].strip(",.!?")
        note = 440*2**((slot["midi_note_written"]+assembly["note_octave_shift"]-69)/12)
        f0 = data["score_f0"][mask]
        require(np.all((f0 == 0) | np.isclose(f0, note)), f"Score F0 mismatch in slot {index}")
        row = {"slot_id": index, "line": line+1, "syllable": slot["syllable"], "word": word,
               "target_s": [start, end], "note_hz": note, "source_window_s": slot["source_window"],
               "mapped_source_centers_s": [float(local[0]), float(local[-1])],
               "original_core_s": slot["vowel_window"], "effective_core_s": [vs, ve],
               "mapped_core_ms": float(core.sum()*STEP*1000),
               "source_core_voiced_fraction": float(cues["voiced"][observed].mean()),
               "source_core_rms_dbfs_p10_p50_p90": quantiles(cues["rms_dbfs"][observed]),
               "source_core_hf_dbfs_p10_p50_p90": quantiles(cues["hf_dbfs"][observed]),
               "source_core_shape_change_p10_p50_p90": quantiles(cues["change"][observed]),
               "phones": []}
        for symbol, lo, hi in phones[line]["phones"]:
            a, b = slot["source_window"]
            if hi <= min(a, local[0]) or lo >= max(b, local[-1]):
                continue
            m = in_window(local, lo, hi)
            src = in_window(cues["t"], lo, hi)
            row["phones"].append({"label": symbol, "marker": symbol in MARKERS, "source_s": [lo, hi],
                                  "mapped_ms": float(m.sum()*STEP*1000),
                                  "mapped_core_ms": float((m & core).sum()*STEP*1000),
                                  "onset_change_near_label": acoustic_boundary(cues, lo),
                                  "end_change_near_label": acoustic_boundary(cues, hi),
                                  "source_voiced_fraction": float(cues["voiced"][src].mean()),
                                  "source_hf_dbfs_median": float(np.median(cues["hf_dbfs"][src]))})
            if symbol == "p" and word in {"shop", "crop"}:
                row["p_release_candidates"] = release_candidate(cues, lo, hi, local)
        if word == "crop":
            row["offline_core_control"] = crop_control(row, local, cues, source["duration"])
        reports.append(row)
    require(np.array_equal(ids, expected_ids), "Saved slot IDs differ from the timing map")
    require(np.all(data["score_f0"][ids == -1] == 0), "Score F0 found in a rest")
    return reports


def audit(work):
    trial = work/"exports/P003/neural-tuning/borisov-verse3-full-v1"
    v5 = work/"exports/P003/verse-3-trial/v5"
    hashes = {}

    def verify(path, expected=None):
        digest = sha(path)
        if expected is not None:
            require(digest == expected, f"SHA-256 mismatch: {path.name}")
        hashes[path.name] = {"sha256": digest, "reference_verified": expected is not None}
        return path

    profile = read_json(ROOT/"pilots/P003/voices.json")["actor_identity_model"]["full_verse3_trial"]
    assembly = read_json(verify(trial/"assembly.json", profile["manifest_sha256"]))
    for row in read_csv(ROOT/"pilots/P003/artifacts.csv"):
        if row["id"] in {"P003-A68", "P003-A69"}:
            verify(work/row["file"], row["sha256"])
    require({"vocal.wav", "mix.wav"} <= hashes.keys(), "Missing A68/A69 in registry")
    generation = read_json(verify(v5/"generation.json", assembly["timing_map_sha256"]))
    verify(ROOT/"pilots/P003/music/score.json", assembly["score_sha256"])
    phones = read_json(verify(work/"reports/P003/verse-3-trial/phones-v5.json", assembly["phone_map_sha256"]))
    require([p["text"] for p in phones] == generation["text"], "Source line texts differ")
    source_audio = []
    for number, source in enumerate(assembly["sources"], 1):
        require(source["line"] == number, "Source line order differs")
        x, rate = audio(verify(v5/f"spoken-line-{number}.wav", source["sha256"]))
        require(abs(len(x)/rate - source["duration"]) <= 1/16000, "Source WAV length differs")
        source_audio.append(source_cues(x, rate))
    native, rate = audio(verify(trial/"native-vocal.wav", assembly["native_vocal_sha256"]))
    dry, dry_rate = audio(trial/"vocal.wav")
    require(rate == dry_rate == RATE, "Unexpected full-v1 waveform rate")
    with np.load(verify(trial/"conditioning.npz"), allow_pickle=False) as archive:
        data = {key: archive[key] for key in ("target_times", "mapped_source_seconds", "score_f0",
                                              "slot_ids", "semantic_features", "generated_mel")}
    n = assembly["frame_count"]
    expected_shapes = [(n,), (n,), (n,), (n,), (1, n, 768), (1, BANDS, n)]
    for (key, value), shape in zip(data.items(), expected_shapes, strict=True):
        require(value.shape == shape and np.isfinite(value).all(), f"Invalid {key}")
    require(len(native) == n*HOP and np.allclose(data["target_times"], (np.arange(n)+.5)*STEP,
                                                rtol=0, atol=1e-9), "Native/target time grid mismatch")
    slots = audit_slots(data, generation, assembly, phones, source_audio)
    jumps = []
    mapped = data["mapped_source_seconds"]
    for i in np.flatnonzero(np.diff(mapped) < -1e-9):
        jumps.append({"target_s": float(data["target_times"][i+1]),
                      "from_to_slots": data["slot_ids"][i:i+2].tolist(),
                      "source_delta_ms": float(1000*(mapped[i+1]-mapped[i]))})
    return {"inputs": hashes, "arrays": {k: list(v.shape) for k, v in data.items()},
            "target_step_ms": STEP*1000, "backward_source_steps": jumps,
            "vowels": vowel_audit(data, assembly, slots, native, dry),
            "slots": slots, "interpretation": [
                "Час джерела у слотах відносний до spoken-line-N.wav. Тривалість на виході оцінена за центрами кадрів.",
                "Piper дає приблизні мітки, включно з наголосом і пунктуацією. DIO, зміна спектральної форми й сплески ВЧ — акустичні ознаки для перевірки меж на слух.",
                "Для межі мітки наведено найбільшу локальну зміну форми спектра в межах ±20 мс. Вікно Hann 16 мс, крок близько 2 мс, порівняння спектрів через 12 мс. Слабкий максимум або максимум на краю вікна не визначає межі фонеми.",
                "Кандидат релізу /p/ має локальний максимум приросту рівня у смузі вище 2 кГц на ≥6 дБ за 10 мс і рівень ≥−60 dBFS. Пошук охоплює мітку, 75 мс перед нею і 90 мс після неї, у межах WAV.",
                "Для crop додатково перераховано лише прив’язку ядра до середніх 80% мітки /ɑ/ зі збереженими межами атаки й релізу на виході. Обидва вікна виміряно на spoken WAV. Це перевірка карти перед слуховою пробою.",
                "Спектральні центроїди для 300–1000 і 1000–2500 Гц та піки поруч із гармоніками допускають кілька причин. Mel зберігає модуль спектра без фази.",
                "A69 містить гітару. Вимірювання голосу виконані на native та A68. Для NPZ збережено поточний SHA. У маніфесті генерації контрольного значення для NPZ немає."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, help="Корінь із exports/P003 та reports/P003")
    parser.add_argument("--output", type=Path, help="Новий зовнішній JSON, типово reports/P003/audit-A68-A69.json")
    args = parser.parse_args()
    try:
        work = args.work_dir
        session = ROOT/"local/p003-session.json"
        if work is None and session.is_file() and not os.environ.get("DUB_WORK_DIR", "").strip():
            work = Path(read_json(session)["work_dir"])
        work = work or external_work_directory()
        require(work is not None, "Specify --work-dir or DUB_WORK_DIR")
        output = protect_source_directories(args.output or work/"reports/P003/audit-A68-A69.json")
        require(output.suffix.lower() == ".json", "Output must be a new .json file")
        require(not output.exists(), f"Output already exists: {output}")
        report = audit(work)
        serialized = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as handle:
            handle.write(serialized + "\n")
        print(f"{output} ({len(report['slots'])} slots)")
    except (OSError, KeyError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
