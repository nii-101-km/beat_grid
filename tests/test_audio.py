import io
import unittest

import numpy as np
import soundfile as sf

from beat_grid import analyze, render_alignment


class AudioTests(unittest.TestCase):
    def setUp(self):
        self.sr = 8000
        rng = np.random.default_rng(42)
        self.audio = rng.uniform(-0.3, 0.3, (self.sr * 4, 2)).astype('float32')
        buffer = io.BytesIO()
        sf.write(buffer, self.audio, self.sr, format='WAV', subtype='FLOAT')
        self.data = buffer.getvalue()

    def test_shift_preserves_material_outside_selection(self):
        first, last = self.sr, self.sr * 3
        for shift_ms in (-80, 0, 80):
            with self.subTest(shift_ms=shift_ms):
                n = round(shift_ms * self.sr / 1000)
                result, sr = sf.read(io.BytesIO(render_alignment(
                    self.data, 196, 197, 199, shift_ms)), dtype='float32', always_2d=True)
                self.assertEqual(sr, self.sr)
                self.assertEqual(len(result), len(self.audio) + n)
                np.testing.assert_array_equal(result[:first], self.audio[:first])
                np.testing.assert_array_equal(result[last+n:], self.audio[last:])

    def test_invalid_selection_and_shift_rejected(self):
        for start, end, shift in ((197, 196, 0), (195, 197, 0), (197, 199, 2001)):
            with self.subTest(start=start, end=end, shift=shift):
                with self.assertRaises(ValueError):
                    render_alignment(self.data, 196, start, end, shift)

    def test_silent_audio_does_not_claim_beats(self):
        buffer = io.BytesIO()
        sf.write(buffer, np.zeros(self.sr * 4), self.sr, format='WAV', subtype='FLOAT')
        with self.assertRaises(ValueError):
            analyze(buffer.getvalue())


if __name__ == '__main__':
    unittest.main()
