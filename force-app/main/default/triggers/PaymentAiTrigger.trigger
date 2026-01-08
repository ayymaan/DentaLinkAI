trigger PaymentAiTrigger on Payment__c (after insert, after update) {
    Set<Id> targetIds = new Set<Id>();

    if (Trigger.isAfter && Trigger.isInsert) {
        for (Payment__c rec : Trigger.new) {
            if (rec.Needs_AI__c == true) {
                targetIds.add(rec.Id);
            }
        }
    }

    if (Trigger.isAfter && Trigger.isUpdate) {
        for (Payment__c rec : Trigger.new) {
            Payment__c oldRec = Trigger.oldMap.get(rec.Id);
            if (rec.Needs_AI__c == true && oldRec.Needs_AI__c != true) {
                targetIds.add(rec.Id);
            }
        }
    }

    for (Id targetId : targetIds) {
        System.enqueueJob(new PaymentAiScoreJob(targetId));
    }
}
