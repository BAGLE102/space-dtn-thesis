"""Ring Road轉換必須清楚記錄單位，不刪短contact、不更改方向。"""
from fractions import Fraction as F
from pathlib import Path
import tempfile
import unittest

from src.ppt_validation.prepare_ring_road import convert_contacts, prepare


class RingRoadPreparationChecks(unittest.TestCase):
    def test_keep_short_windows_and_both_directions(self):
        text=('a contact +1 +3 7 32 12500\n'
              'a contact +1 +3 32 7 12500\n'
              'a contact +0 +86400 48 1 125000000\n'
              'a range +0 +86400 7 32 0\n')
        contacts,audit=convert_contacts(text)
        self.assertEqual(len(contacts),2)
        self.assertEqual([(c['source'],c['target']) for c in contacts],[('7','32'),('32','7')])
        self.assertEqual(contacts[0]['id'],'rrn_0001')
        self.assertEqual(F(contacts[0]['rate']),F(1,10))
        self.assertEqual(F(contacts[0]['remaining_capacity']),F(1,5))
        self.assertEqual(audit['removed_server_contacts'],1)
        self.assertEqual(audit['original_rates_bytes_s'],['12500'])

    def test_modified_source_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'changed.txt'; p.write_text('changed',encoding='utf-8')
            out=Path(directory)/'out'
            with self.assertRaisesRegex(ValueError,'SHA256'):
                prepare(p,out)
            self.assertFalse(out.exists())


if __name__=='__main__':
    unittest.main()
