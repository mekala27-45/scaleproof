import type {Plan,Check} from './types';
export const defaultPlan:Plan={schema_version:1,low_rps:2,high_rps:10,duration_seconds:720,warmup_seconds:60,high_start_seconds:180,high_end_seconds:480,min_replicas:1,max_replicas:3,request_timeout_seconds:5};
export function preview(p:Plan):Check {
 const keys=Object.keys(defaultPlan) as (keyof Plan)[];
 if(Object.keys(p).length!==keys.length||keys.some(k=>typeof p[k]!=='number'||!Number.isFinite(p[k])||Math.abs(p[k])>1e9)||p.schema_version!==1||keys.filter(k=>!['low_rps','high_rps','request_timeout_seconds'].includes(k)).some(k=>!Number.isInteger(p[k])))throw Error('Use exactly the numeric workload fields, whole seconds and whole replica counts.');
 const phases=0<=p.warmup_seconds&&p.warmup_seconds<p.high_start_seconds&&p.high_start_seconds<p.high_end_seconds&&p.high_end_seconds<p.duration_seconds;
 const high=p.high_end_seconds-p.high_start_seconds;
 function decimal(value:number):[bigint,bigint]{const [mantissa,exponent='0']=String(value).split('e');const digits=mantissa.split('.');const coefficient=BigInt(digits.join(''));const power=Number(exponent)-(digits[1]?.length||0);return power>=0?[coefficient*10n**BigInt(power),1n]:[coefficient,10n**BigInt(-power)]}
 function exactBudget(){const [low,ld]=decimal(p.low_rps),[highRate,hd]=decimal(p.high_rps);const denominator=ld*hd;const numerator=low*BigInt(p.duration_seconds-high)*hd+highRate*BigInt(high)*ld;return Number((numerator+denominator-1n)/denominator)}
 const budget=phases&&p.low_rps>0&&p.high_rps>0?exactBudget():null;
 const rules=[{rule:'rate',passed:p.low_rps>0&&p.low_rps<=p.high_rps&&p.high_rps<=100,message:'Positive ordered rates, up to 100 requests/s.'},{rule:'duration',passed:p.duration_seconds>0&&p.duration_seconds<=900,message:'Duration up to 900 seconds.'},{rule:'phases',passed:phases,message:'Warmup < high start < high end < duration.'},{rule:'replicas',passed:p.min_replicas>=1&&p.min_replicas<=p.max_replicas&&p.max_replicas<=3,message:'One to three replicas.'},{rule:'deadline',passed:p.request_timeout_seconds>=1&&p.request_timeout_seconds<=10,message:'Deadline from 1 to 10 seconds.'},{rule:'arrival_budget',passed:budget!==null&&budget<=50000,message:'Integrated-rate budget at most 50000 arrivals.'}];
 return {decision:rules.every(r=>r.passed)?'accepted':'rejected',rules,expected_arrival_budget:budget,execution_mode:'deterministic_local'};
}
