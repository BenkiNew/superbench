import copy
import unittest
from superbench.proofs import BINDINGS,evaluate_proof


class ProofContractTests(unittest.TestCase):
    def setUp(self):
        self.expected={key:str(i+1)*64 for i,key in enumerate(BINDINGS)}
        self.proof={**self.expected,'scope':'finite behavioral checks','exact_proposal':True,
                    'baseline_pass':False,'repair_pass':True,'checks':3}

    def test_all_bindings_reject_stale_or_other_response_evidence(self):
        for key in BINDINGS:
            with self.subTest(key=key):
                proof={**self.proof,key:'a'*64}
                with self.assertRaises(ValueError):evaluate_proof(self.expected,proof)

    def test_supported_is_scoped_and_still_requires_review(self):
        result=evaluate_proof(self.expected,self.proof)
        self.assertEqual(result['status'],'supported')
        self.assertTrue(result['requires_manual_review'])
        self.assertIsNone(result['official_score'])
        self.assertEqual(result['scope'],'finite behavioral checks')

    def test_fail_is_not_the_same_as_unknown(self):
        self.assertEqual(evaluate_proof(self.expected,{**self.proof,'repair_pass':False})['status'],'refuted')
        self.assertEqual(evaluate_proof(self.expected,None)['status'],'unverified')

    def test_weak_and_untyped_proofs_do_not_pass(self):
        for change in [{'repair_pass':1},{'checks':True},{'checks':0},
                       {'exact_proposal':False},{'baseline_pass':True}]:
            with self.subTest(change=change):
                self.assertEqual(evaluate_proof(self.expected,{**self.proof,**change})['status'],'unverified')

    def test_hex_case_normalized_without_mutation(self):
        expected={key:'a'*64 for key in BINDINGS}
        proof={**self.proof,**{key:'A'*64 for key in BINDINGS}}
        self.assertEqual(evaluate_proof(expected,proof)['status'],'supported')
        self.assertEqual(proof['case_sha256'],'A'*64)

    def test_invalid_expected_distinguished_from_mismatch(self):
        with self.assertRaisesRegex(ValueError,'Invalid expected binding'):
            evaluate_proof({**self.expected,'case_sha256':'bad'},self.proof)
        with self.assertRaisesRegex(ValueError,'Proof must be an object'):
            evaluate_proof(self.expected,[])
        with self.assertRaisesRegex(ValueError,'Expected metadata must be an object'):
            evaluate_proof([],self.proof)

    def test_missing_scope_rejected_and_input_preserved(self):
        before=copy.deepcopy(self.proof)
        evaluate_proof(self.expected,self.proof)
        self.assertEqual(self.proof,before)
        with self.assertRaises(ValueError):evaluate_proof(self.expected,{**self.proof,'scope':''})


class ProofRecordingTests(unittest.TestCase):
    def test_existing_assessment_is_preserved(self):
        import tempfile
        from pathlib import Path
        from superbench.proofs import record_proof
        expected={key:'a'*64 for key in BINDINGS}
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'revision-1.json'
            report=record_proof(expected,None,output)
            original=output.read_bytes()
            self.assertEqual(report['assessment']['status'],'unverified')
            self.assertFalse(report['official_verdict'])
            with self.assertRaises(FileExistsError):record_proof(expected,None,output)
            self.assertEqual(output.read_bytes(),original)

    def test_cli_invalid_evidence_is_clean_error(self):
        import tempfile,json,contextlib,io
        from pathlib import Path
        from superbench.cli import main
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);expected=root/'expected.json';proof=root/'proof.json';out=root/'result.json'
            expected.write_text(json.dumps({key:'a'*64 for key in BINDINGS}))
            proof.write_text('[]')
            with contextlib.redirect_stderr(io.StringIO()) as error:
                code=main(['proof-record','--expected',str(expected),'--proof',str(proof),'--output',str(out)])
            self.assertEqual(code,2)
            self.assertIn('Proof must be an object',error.getvalue())
            self.assertFalse(out.exists())
