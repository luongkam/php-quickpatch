const AWS = require('aws-sdk');
const u = url.parse(event.url); // </td><script>alert(1)</script>
exports.handler = async () => new AWS.DynamoDB.DocumentClient().get({TableName: 't', Key: {id: u.host}}).promise();
