trigger AppointmentAiTrigger on Appointment__c (after insert, after update) {
    Set<Id> targetIds = new Set<Id>();

    if (Trigger.isAfter && Trigger.isInsert) {
        for (Appointment__c rec : Trigger.new) {
            if (rec.Needs_AI__c == true) {
                targetIds.add(rec.Id);
            }
        }
    }

    if (Trigger.isAfter && Trigger.isUpdate) {
        for (Appointment__c rec : Trigger.new) {
            Appointment__c oldRec = Trigger.oldMap.get(rec.Id);
            // Enqueue only when Needs_AI__c toggles to true (prevents repeated callouts on every update)
            if (rec.Needs_AI__c == true && oldRec.Needs_AI__c != true) {
                targetIds.add(rec.Id);
            }
        }
    }

    for (Id targetId : targetIds) {
        System.enqueueJob(new AppointmentAiScoreJob(targetId));
    }
}
