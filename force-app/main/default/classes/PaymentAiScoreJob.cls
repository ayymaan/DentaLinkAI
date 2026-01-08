public with sharing class PaymentAiScoreJob implements Queueable, Database.AllowsCallouts {
    private Id recordId;

    public PaymentAiScoreJob(Id recordId) {
        this.recordId = recordId;
    }

    public void execute(QueueableContext context) {
        List<Payment__c> payments = [
            SELECT Id, Amount__c, DaysOverdue__c, Method__c,
                   Predicted_Late__c, LatePaymentRisk__c,
                   Needs_AI__c, Ai_LastError__c
            FROM Payment__c
            WHERE Id = :recordId
            LIMIT 1
        ];
        if (payments.isEmpty()) {
            return;
        }
        Payment__c payment = payments[0];

        try {
            HttpRequest req = new HttpRequest();
            req.setEndpoint('callout:DL_AI_API/predict/payment');
            req.setMethod('POST');
            req.setHeader('Content-Type', 'application/json');

            Map<String, Object> payload = new Map<String, Object>{
                'amount' => payment.Amount__c,
                'days_overdue' => payment.DaysOverdue__c,
                'method' => payment.Method__c
            };
            req.setBody(JSON.serialize(payload));

            HttpResponse res = new Http().send(req);

            if (res.getStatusCode() >= 200 && res.getStatusCode() < 300) {
                Map<String, Object> body = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
                payment.Predicted_Late__c = (Boolean) body.get('predicted_late');

                Object score = body.get('risk_score');
                // NOTE: This stores the score as a percentage (0-100). Remove '* 100' if your field expects 0-1.
                payment.LatePaymentRisk__c = score == null ? null : Decimal.valueOf(String.valueOf(score)) * 100;

                payment.Ai_LastError__c = null;
                payment.Needs_AI__c = false;
            } else {
                payment.Ai_LastError__c = 'HTTP ' + res.getStatusCode() + ': ' + res.getBody();
            }
        } catch (Exception ex) {
            payment.Ai_LastError__c = ex.getMessage();
        }

        Database.update(payment, false);
    }
}
