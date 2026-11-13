import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import ezdxf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from cad_edit_workbench import CadEditSession, ConflictError, sha


class EditingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source.dxf'
        doc = ezdxf.new('R2010')
        m = doc.modelspace()
        self.text = m.add_text('C12', dxfattribs={'insert': (20, 30)}).dxf.handle
        self.line = m.add_line((0, 0), (100, 0)).dxf.handle
        dim = m.add_linear_dim(base=(0, 10), p1=(0, 0), p2=(100, 0))
        dim.render()
        self.dim = dim.dimension.dxf.handle
        doc.saveas(self.source)
        self.original = sha(self.source)
        self.s = CadEditSession.create(self.source, self.root / 'session')
        self.rev = self.s.inspect()['revision']

    def tearDown(self):
        self.tmp.cleanup()

    def test_multiple_edits_and_restore(self):
        first = self.s.move(self.text, 5, -3, expected_revision=self.rev)
        drawing = Path(self.s.inspect()['drawing'])
        self.assertEqual(tuple(ezdxf.readfile(drawing).entitydb[self.text].dxf.insert), (25, 27, 0))
        second = self.s.move(self.dim, 0, 15, expected_revision=first)
        doc = ezdxf.readfile(self.s.inspect()['drawing'])
        self.assertEqual(doc.entitydb[self.dim].get_measurement(), 100)
        self.assertEqual(doc.entitydb[self.dim].dxf.defpoint.y, 25)
        undone = self.s.undo(expected_revision=second)
        self.assertEqual(sha(self.s.inspect()['drawing']), sha(drawing))
        self.s.undo(expected_revision=undone)
        self.assertEqual(sha(self.s.inspect()['drawing']), self.original)
        self.assertEqual(sha(self.source), self.original)
        self.assertIn('<svg', Path(self.s.inspect()['preview']).read_text(encoding='utf-8'))

    def test_stale_revision(self):
        self.s.move(self.text, 1, 0, expected_revision=self.rev)
        with self.assertRaises(ConflictError):
            self.s.move(self.text, 2, 0, expected_revision=self.rev)

    def test_manual_change_blocks_undo(self):
        rev = self.s.move(self.text, 1, 0, expected_revision=self.rev)
        p = Path(self.s.inspect()['drawing'])
        doc = ezdxf.readfile(p)
        doc.entitydb[self.text].dxf.text = 'MANUAL'
        doc.saveas(p)
        with self.assertRaises(ConflictError):
            self.s.undo(expected_revision=rev)

    def test_geometry_not_editable(self):
        with self.assertRaises(ValueError):
            self.s.move(self.line, 10, 0, expected_revision=self.rev)
        self.assertEqual(self.s.inspect()['revision'], self.rev)

    def test_failed_preview_does_not_commit(self):
        with patch('cad_edit_workbench.render', side_effect=RuntimeError('render failure')):
            with self.assertRaises(RuntimeError):
                self.s.move(self.text, 1, 0, expected_revision=self.rev)
        self.assertEqual(self.s.inspect()['revision'], self.rev)

    def test_lock(self):
        with self.s._lock():
            with self.assertRaises(ConflictError):
                self.s.move(self.text, 1, 0, expected_revision=self.rev)

    def test_invalid_offset(self):
        with self.assertRaises(ValueError):
            self.s.move(self.text, float('nan'), 0, expected_revision=self.rev)

    def test_missing_handle_and_empty_undo(self):
        with self.assertRaises(ValueError):
            self.s.move('FFFF', 1, 0, expected_revision=self.rev)
        with self.assertRaises(ValueError):
            self.s.undo(expected_revision=self.rev)

    def test_mtext_and_aligned(self):
        doc = ezdxf.readfile(self.source)
        text = doc.modelspace().add_mtext('Cột C12', dxfattribs={'insert': (0, 30)})
        dim = doc.modelspace().add_aligned_dim(p1=(0, 0), p2=(30, 40), distance=5)
        dim.render()
        doc.saveas(self.source)
        s = CadEditSession.create(self.source, self.root / 'second')
        rev = s.move(text.dxf.handle, 2, 3, expected_revision=s.inspect()['revision'])
        s.move(dim.dimension.dxf.handle, -4, 3, expected_revision=rev)
        reopened = ezdxf.readfile(s.inspect()['drawing'])
        self.assertAlmostEqual(reopened.entitydb[dim.dimension.dxf.handle].get_measurement(), 50)
        self.assertEqual(reopened.entitydb[text.dxf.handle].text, 'Cột C12')


if __name__ == '__main__':
    unittest.main()
