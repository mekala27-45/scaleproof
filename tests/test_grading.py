import copy
import unittest
from scaleproof.common import digest
from scaleproof.grading import grade_run, replica_seconds, percentile


def fixture():
    plans = [dict(id=f"r{i}", scheduled_seconds=200+i, phase="high", query_id="q", query="test") for i in range(2)]
    identity = dict(model_digest="m", corpus_digest="c", source_revision="s", image_identity="i", timeout_seconds=5)
    ledger=[]
    for i,row in enumerate(plans):
        receipt={**identity, "request_id":row["id"], "pod_uid":f"pod-{i}", "encoder_invocations":1, "execution_mode":"actual_cpu_inference", "input_digest":digest("test"),"results":[],"output_digest":digest([])}
        ledger.append({**row, "request_id":row["id"], "status":"completed", "dispatched_seconds":row["scheduled_seconds"], "finished_seconds":row["scheduled_seconds"]+.1, "receipt":receipt})
    obs=[dict(seconds=t, ready=2 if 200<=t<550 else 1, desired=2 if 190<=t<540 else 1, metrics_age_seconds=1, hpa_active=True) for t in range(0,721,10)]
    events=[dict(event=e,request_id=r["id"]) for r in plans for e in ("admitted","finished")]
    return [dict(rows=plans,schedule_digest=digest(plans)), ledger, obs, identity,"hpa",events]


class GradingTests(unittest.TestCase):
    def test_clean_and_absent(self):
        self.assertEqual(grade_run(*fixture())["status"],"done")
        self.assertEqual(grade_run({},[],[],{},"hpa")["status"],"not_done")

    def test_six_adversarial_bundles(self):
        for kind in range(6):
            args=fixture()
            if kind==0: args[1].pop()
            if kind==1: args[1].append(copy.deepcopy(args[1][0]))
            if kind==2: args[1][0]["receipt"]["model_digest"]="wrong"
            if kind==3:
                for row in args[2]: row["ready"]=1
            if kind==4: args[2][1]["metrics_age_seconds"]=46
            if kind==5:
                for row in args[2]: row["desired"]=row["ready"]=1
            with self.subTest(kind=kind): self.assertEqual(grade_run(*args)["status"],"not_done")

    def test_known_step_integral_and_percentiles(self):
        self.assertEqual(replica_seconds([{"seconds":0,"ready":1},{"seconds":10,"ready":3},{"seconds":30,"ready":1}],5,25),50)
        self.assertIsNone(percentile([1,2],.95,20))
        self.assertEqual(percentile(list(range(1,101)),.95,20),95)

    def test_late_completion_never_success(self):
        args=fixture()
        args[1][0]["status"]="timeout"
        report=grade_run(*args)
        self.assertEqual(report["metrics"]["late_completions"],1)
        self.assertEqual(report["metrics"]["phases"]["high"]["deadline_success_fraction"],.5)

    def test_dispatch_failure_keeps_denominator(self):
        args=fixture(); args[1][0]["status"]="dispatch_failure"
        report=grade_run(*args)
        self.assertEqual(report["metrics"]["phases"]["high"]["scheduled"],2)
        self.assertEqual(report["status"],"not_done")
