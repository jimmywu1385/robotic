'use strict';
     
const AWS = require('aws-sdk');

AWS.config.update({region: "ap-northeast-1",});

const docClient = new AWS.DynamoDB.DocumentClient();
const sqs = new AWS.SQS({apiVersion: '2012-11-05'});

 const crypto = require('crypto')

// Close dialog with the customer, reporting fulfillmentState of Failed or Fulfilled ("Thanks, your pizza will arrive in 20 minutes")
function close(sessionAttributes, fulfillmentState, message) {
    return {
        sessionAttributes,
        dialogAction: {
            type: 'Close',
            fulfillmentState,
            message,
        },
    };
}

function elicitSlot(sessionAttributes, intentName, slots, slotToElicit, message) {
     return {
        sessionAttributes,
        dialogAction: {
            type: 'ElicitSlot',
            intentName,
            slots,
            slotToElicit,
            message,
         
        },
    };
}

function confirmIntent(sessionAttributes, fulfillmentState, url, message){
    return{
        sessionAttributes,
        dialogAction: {
            type: 'Close',
            fulfillmentState,
            message,
            responseCard: {
                version: 1,
                contentType: 'application/vnd.amazonaws.card.generic',
                genericAttachments: [{
                    // title: 'Mission accomplished!',
                    // subTitle: 'Mission accomplished!',
                    imageUrl: url,
                    //attachmentLinkUrl: url,
                    // buttons:[{
                    //     text: 'Good job!',
                    //     value: 'Good job'
                    // }]
                }]
            } 
        }
    }
}

function recordTime(pet, time, date) {
    var params = {
        TableName:'testTable',
        Key:{
            "pet": pet
        },
        UpdateExpression: "SET #a = :vals",
        ExpressionAttributeNames:{
            "#a": "RECORD"
        },
        ExpressionAttributeValues: {
            ":vals": [date, time]
        }
    };
    console.log("updating feeding record...");
    docClient.update(params).promise();
}

function scheduleJob(pk, sk, pet, task) {
    var detail = {
        "pet" : pet,
        "task" : task
    }
    var params = {
        TableName:'JobsTable',
        Item:{
            "pk": pk,
            "sk": sk,
            "detail": detail,
            "detail_type": "job-reminder"
        }
    };
    docClient.put(params).promise();
}

function todo(pet, time, date) {
    var params = {
        TableName:'testTable',
        Key:{
            "pet": pet
        },
        UpdateExpression: "SET #a = list_append(#a, :vals)",
        ExpressionAttributeNames:{
            "#a": "TODO"
        },
        ExpressionAttributeValues: {
            ":vals": [[date, time]]
        }
    };
    console.log("Adding todo list...");
    docClient.update(params).promise();

}

async function querydb(pet) {
    var params = {
        TableName : 'testTable',
        KeyConditionExpression: "pet = :ppp",
        // ExpressionAttributeNames:{
        //     "#yr": "year"
        // },
        ExpressionAttributeValues: {
            ":ppp": pet,
            //":tttt": task
        }
    };
    var result = await docClient.query(params).promise()
    return [result.Items[0].RECORD[0], result.Items[0].RECORD[1]]
    
}
    
// --------------- Events -----------------------
 
async function dispatch(intentRequest, callback) {
    console.log(`request received for userId=${intentRequest.userId}, intentName=${intentRequest.currentIntent.name}`);
    const sessionAttributes = intentRequest.sessionAttributes;
    const slots = intentRequest.currentIntent.slots;

    if(intentRequest.currentIntent.name == 'OrderPizza'){
        console.log('feed');
        //feed now
        //if (slots.time == null && slots.date == null){
        if (slots.now == 'now'){
            let date_string = new Date().toLocaleString("en-US", { timeZone: "Asia/Taipei" });
            let date_nz = new Date(date_string);
            let year = date_nz.getFullYear();
            let month = ("0" + (date_nz.getMonth() + 1)).slice(-2);
            let date = ("0" + date_nz.getDate()).slice(-2);
            let hours = ("0" + date_nz.getHours()).slice(-2);
            let minutes = ("0" + date_nz.getMinutes()).slice(-2);
            let seconds = ("0" + date_nz.getSeconds()).slice(-2);
            let date_yyyy_mm_dd = year + "-" + month + "-" + date;
            //console.log("Date in YYYY-MM-DD format: " + date_yyyy_mm_dd);
            let time_hh_mm = hours + ":" + minutes;
            //console.log("Time in hh:mm:ss format: " + time_hh_mm);
            if(slots.task == 'feed' || slots.task == 'water'){
                recordTime(slots.pet, time_hh_mm, date_yyyy_mm_dd)    
            }
            var params = {
                MessageAttributes: {
                    "pet": {
                      DataType: "String",
                      StringValue: slots.pet
                    },
                    "task": {
                      DataType: "String",
                      StringValue: slots.task
                    }
                },
              MessageBody: crypto.randomUUID(),
              // MessageDeduplicationId: "TheWhistler",
              MessageGroupId: "Group1",  // Required for FIFO queues
              QueueUrl: "https://sqs.ap-northeast-1.amazonaws.com/739183738838/pizzaQueue.fifo"
            };
            
            sqs.sendMessage(params, function(err, data) {
              if (err) {
                console.log("Error", err);
              } else {
                console.log("Success", data.MessageId);
              }
            });
            if(slots.task == 'feed' || slots.task == 'water'){
                callback(close(sessionAttributes, 'Fulfilled',
                {'contentType': 'PlainText', 'content': `Okay, I am going to ${slots.task} your ${slots.pet}.`}));  
            }
            else{
                callback(close(sessionAttributes, 'Fulfilled',
                {'contentType': 'PlainText', 'content': `Okay, I am going to ${slots.task} with your ${slots.pet}.`}));   
            }
        }
        //feed later
        else{
            
            if (slots.time == null || slots.time == undefined){
                callback(elicitSlot(sessionAttributes, intentRequest.currentIntent.name, intentRequest.currentIntent.slots, "time",
                { contentType: 'PlainText', content: 'What time is it' }));
            }
            else if (slots.date == null|| slots.date == undefined){
                callback(elicitSlot(sessionAttributes, intentRequest.currentIntent.name, intentRequest.currentIntent.slots, "date",
                { contentType: 'PlainText', content: 'When' })) ;
            }
            else{
                var gmt8 = new Date(slots.date+'T'+slots.time+':00.000+08:00');
                console.log(gmt8)
                gmt8.toISOString()
                let _year = gmt8.getFullYear();
                let _month = ("0" + (gmt8.getMonth() + 1)).slice(-2);
                let _date = ("0" + gmt8.getDate()).slice(-2);
                let _hours = ("0" + gmt8.getHours()).slice(-2);
                let _minutes = ("0" + gmt8.getMinutes()).slice(-2);
                let _minutes5 = ("0" + (gmt8.getMinutes() - gmt8.getMinutes()%5)).slice(-2);
                let _seconds = ("0" + gmt8.getSeconds()).slice(-2);
                let date_yyyy_mm_dd = _year + "-" + _month + "-" + _date;
                console.log("Date in YYYY-MM-DD format: " + date_yyyy_mm_dd);
                let time_hh_mm = _hours + ":" + _minutes;
                console.log(time_hh_mm)
                let time5 = _hours + ":" + _minutes5;
                
                var sk = (date_yyyy_mm_dd+'T'+time_hh_mm+':00.000Z');
                var pk = ('j#'+date_yyyy_mm_dd+'T'+time5);
                scheduleJob(pk, sk, slots.pet, slots.task)
                callback(close(sessionAttributes, 'Fulfilled',
                {'contentType': 'PlainText', 'content': `Okay, I will ${slots.task} your ${slots.pet} at ${slots.time} on ${slots.date}`}));   
            }
                
        }
    }
    else if(intentRequest.currentIntent.name == 'getImage'){
        var url;
        var queueURL = 'https://sqs.ap-northeast-1.amazonaws.com/739183738838/TestQueue.fifo';
        
        var params = {
            AttributeNames: [
                "SentTimestamp"
            ],
            MaxNumberOfMessages: 1,
            MessageAttributeNames: [
                "All"
            ],
            QueueUrl: queueURL,
            VisibilityTimeout: 10,
            WaitTimeSeconds: 0
        };
        var loop = true;
        while(loop){
            await sqs.receiveMessage(params, function(err, data) {
                if (err) {
                    console.log("Receive Error", err);
                }
                else if (data.Messages) {
                    url = data.Messages[0].Body
                    var deleteParams = {
                        QueueUrl: queueURL,
                        ReceiptHandle: data.Messages[0].ReceiptHandle
                    };
                    sqs.deleteMessage(deleteParams, function(err, data) {
                        if (err) {
                            console.log("Delete Error", err);
                        } 
                        else {
                            console.log("Message Deleted", data);
                        }
                    });
                    loop = false;
                }
            }).promise();
        }
        
        callback(confirmIntent(sessionAttributes, 'Fulfilled', url, {contentType: 'PlainText', content: 'Sure'}));  
    }
    else if(intentRequest.currentIntent.name == 'recordTime'){
        console.log(slots.time);
        if (slots.pet == null || slots.pet == undefined){
            callback(elicitSlot(sessionAttributes, intentRequest.currentIntent.name, intentRequest.currentIntent.slots, "pet",
            { contentType: 'PlainText', content: 'Which pet?' })) ;
        }
        else if (slots.time == null || slots.time == undefined){
            callback(elicitSlot(sessionAttributes, intentRequest.currentIntent.name, intentRequest.currentIntent.slots, "time",
            { contentType: 'PlainText', content: 'What time is it?' }));
        }
        else if (slots.date == null || slots.date == undefined){
            callback(elicitSlot(sessionAttributes, intentRequest.currentIntent.name, intentRequest.currentIntent.slots, "date",
            { contentType: 'PlainText', content: 'When?' }));
        }
        else{
            recordTime(slots.pet, slots.time, slots.date)
            callback(close(sessionAttributes, 'Fulfilled',
            {'contentType': 'PlainText', 'content': `Okay, I have recorded the ${slots.taskk} time ${slots.date} ${slots.time}`}));   
        }
    }
    else if(intentRequest.currentIntent.name == 'getTime'){
        var dt = await querydb(slots.pet);
        slots.date = dt[0]
        slots.time = dt[1]
        //querydb(task, pet)
        callback(close(sessionAttributes, 'Fulfilled',
        {'contentType': 'PlainText', 'content': `At ${slots.time} on ${slots.date}`}));
    }
    else{
         callback(close(sessionAttributes, 'Fulfilled',
        {'contentType': 'PlainText', 'content': `intent error`}));
    }
}
 
// --------------- Main handler -----------------------
 
// Route the incoming request based on intent.
// The JSON body of the request is provided in the event slot.
exports.handler = (event, context, callback) => {
    
    try {
        dispatch(event,
            (response) => {
                callback(null, response);
            });
    } catch (err) {
        callback(err);
    }
};