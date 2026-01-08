trigger TreatmentAiTrigger on Treatment__c (after insert, after update) {
    Set<Id> targetIds = new Set<Id>();

    if (Trigger.isAfter && Trigger.isInsert) {
        for (Treatment__c rec : Trigger.new) {
            if (rec.Needs_AI__c == true) {
                targetIds.add(rec.Id);
            }
        }
    }

    if (Trigger.isAfter && Trigger.isUpdate) {
        for (Treatment__c rec : Trigger.new) {
            Treatment__c oldRec = Trigger.oldMap.get(rec.Id);
            if (rec.Needs_AI__c == true && oldRec.Needs_AI__c != true) {
                targetIds.add(rec.Id);
            }
        }
    }

    for (Id targetId : targetIds) {
        System.enqueueJob(new TreatmentAiScoreJob(targetId));
    }
}
