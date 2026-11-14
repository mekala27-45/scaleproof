import type {Plan,Check} from './types';
export const defaultPlan:Plan={schema_version:1,low_rps:2,high_rps:10,duration_seconds:720,warmup_seconds:60,high_start_seconds:180,high_end_seconds:480,min_replicas:1,max_replicas:3,request_timeout_seconds:5};
export function preview(p:Plan):Check {
 const phases=0<=p.warmup_seconds&&p.warmup_seconds<p.high_start_seconds&&p.high_start_seconds<p.high_end_seconds&&p.high_end_seconds<p.duration_seconds;
 const high=p.high_end_seconds-p.high_start_seconds;
 const budget=phases?Math.ceil(p.low_rps*(p.duration_seconds-high)+p.high_rps*high):null;
 const rules=[{rule:'rate',passed:p.low_rps>0&&p.low_rps<=p.high_rps&&p.high_rps<=100,message:'Positive ordered rates, up to 100 requests/s.'},{rule:'duration',passed:p.duration_seconds>0&&p.duration_seconds<=900,message:'Duration up to 900 seconds.'},{rule:'phases',passed:phases,message:'Warmup < high start < high end < duration.'},{rule:'replicas',passed:p.min_replicas>=1&&p.min_replicas<=p.max_replicas&&p.max_replicas<=3,message:'One to three replicas.'},{rule:'deadline',passed:p.request_timeout_seconds>=1&&p.request_timeout_seconds<=10,message:'Deadline from 1 to 10 seconds.'},{rule:'arrival_budget',passed:budget!==null&&budget<=50000,message:'Integrated-rate budget at most 50000 arrivals.'}];
 return {decision:rules.every(r=>r.passed)?'accepted':'rejected',rules,expected_arrival_budget:budget,execution_mode:'deterministic_local'};
}
