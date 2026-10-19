---
document_id: DOC-L7-008
doc_type: incident_report
launch_id: L7-CHARLIE
component_id: IM-03
incident_id: INC-L7-03
related_ids: REC-L7-009;REC-L7-010;REC-L7-011;REC-L7-012;REC-L7-022
occurred_at: 2026-06-21
revision: 1
status: final
synthetic: true
summary_scope: retrospective
---
# Charlie yaw reference anomaly

## Configuration and launch
Before Launch-Deets Charlie launched, inertial measurement unit IM-03 had firmware revision C7 installed. The component record is timed at 10:48 UTC on 21 June 2026 (REC-L7-010). Charlie lifted off from Pad A at 11:00 UTC that day (REC-L7-009; DOC-L7-007).

## Incident observation
At 11:06:09 UTC, after liftoff, IM-03 produced a transient 0.42 degree yaw bias lasting 26 seconds. The incident was classified major and closed (REC-L7-011). The magnitude and duration describe the same yaw event, not two separate incidents.

## Later action and clarification
On 25 June 2026 at 18:30 UTC, firmware C8 was released with a temperature compensation table for IM-03 (REC-L7-012; DOC-L7-009). The C8 corrective action followed the launch; C7 was the configuration documented before liftoff. A separate incident revision dated 26 June clarified that the 0.42 degree bias was measured against the ground reference rather than the onboard estimate (REC-L7-022; DOC-L7-017).

## Evidence scope
The reference clarification did not change the recorded 0.42 degree magnitude. This retrospective synthetic summary links the launch configuration, yaw incident, corrective action and later reference clarification. Supporting records: REC-L7-009, REC-L7-010, REC-L7-011, REC-L7-012, REC-L7-022.
