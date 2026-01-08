public with sharing class AppointmentAiScoreJob implements Queueable, Database.AllowsCallouts {
    private Id recordId;

    public AppointmentAiScoreJob(Id recordId) {
        this.recordId = recordId;
    }

    public void execute(QueueableContext context) {
        List<Appointment__c> appts = [
            SELECT Id, BookingLeadDays__c, Fee__c, Status__c,
                   Predicted_NoShow__c, NoShowRisk__c, RiskLevel__c,
                   Needs_AI__c, Ai_LastError__c
            FROM Appointment__c
            WHERE Id = :recordId
            LIMIT 1
        ];
        if (appts.isEmpty()) {
            return;
        }
        Appointment__c appt = appts[0];

        try {
            HttpRequest req = new HttpRequest();
            req.setEndpoint('callout:DL_AI_API/predict/appointment');
            req.setMethod('POST');
            req.setHeader('Content-Type', 'application/json');

            Map<String, Object> payload = new Map<String, Object>{
                'booking_lead_days' => appt.BookingLeadDays__c,
                'fee' => appt.Fee__c,
                'status' => appt.Status__c
            };
            req.setBody(JSON.serialize(payload));

            HttpResponse res = new Http().send(req);

            if (res.getStatusCode() >= 200 && res.getStatusCode() < 300) {
                Map<String, Object> body = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
                appt.Predicted_NoShow__c = (Boolean) body.get('predicted_no_show');

                Object score = body.get('risk_score');
                // NOTE: This stores the score as a percentage (0-100). Remove '* 100' if your field expects 0-1.
                appt.NoShowRisk__c = score == null ? null : Decimal.valueOf(String.valueOf(score)) * 100;

                appt.RiskLevel__c = (String) body.get('risk_level');
                appt.Ai_LastError__c = null;
                appt.Needs_AI__c = false;
            } else {
                appt.Ai_LastError__c = 'HTTP ' + res.getStatusCode() + ': ' + res.getBody();
            }
        } catch (Exception ex) {
            appt.Ai_LastError__c = ex.getMessage();
        }

        Database.update(appt, false);
    }
}
