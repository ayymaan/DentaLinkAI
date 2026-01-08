public with sharing class TreatmentAiScoreJob implements Queueable, Database.AllowsCallouts {
    private Id recordId;

    public TreatmentAiScoreJob(Id recordId) {
        this.recordId = recordId;
    }

    public void execute(QueueableContext context) {
        List<Treatment__c> treatments = [
            SELECT Id, Cost__c, Status__c, Type__c,
                   UrgencyScore__c, NoteCategory__c, RecommendedNextStep__c,
                   Needs_AI__c, Ai_LastError__c
            FROM Treatment__c
            WHERE Id = :recordId
            LIMIT 1
        ];
        if (treatments.isEmpty()) {
            return;
        }
        Treatment__c treatment = treatments[0];

        try {
            HttpRequest req = new HttpRequest();
            req.setEndpoint('callout:DL_AI_API/predict/treatment');
            req.setMethod('POST');
            req.setHeader('Content-Type', 'application/json');

            Map<String, Object> payload = new Map<String, Object>{
                'cost' => treatment.Cost__c,
                'status' => treatment.Status__c,
                'type' => treatment.Type__c
            };
            req.setBody(JSON.serialize(payload));

            HttpResponse res = new Http().send(req);

            if (res.getStatusCode() >= 200 && res.getStatusCode() < 300) {
                Map<String, Object> body = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());

                Object urgency = body.get('urgency_score');
                treatment.UrgencyScore__c = urgency == null ? null : Decimal.valueOf(String.valueOf(urgency));

                treatment.NoteCategory__c = (String) body.get('note_category');
                treatment.RecommendedNextStep__c = (String) body.get('recommended_next_step');

                treatment.Ai_LastError__c = null;
                treatment.Needs_AI__c = false;
            } else {
                treatment.Ai_LastError__c = 'HTTP ' + res.getStatusCode() + ': ' + res.getBody();
            }
        } catch (Exception ex) {
            treatment.Ai_LastError__c = ex.getMessage();
        }

        Database.update(treatment, false);
    }
}
