## Speakeasy Lambda 

This function ties in with the Speakeasy frontend app I made here: https://github.com/samdev23/speakeasy-app. On the AWS side of this project there is an API websocket gateway with 4 defined routes: connect, disconnect, sendPublicMsg, and setUsername. This lambda function defines these routes. 

All routes expect to receive a json payload over the websocket connection in order to perform their actions, example:
`{"action": "setUsername", "name": "Tom", etc.}`

## Routes
- **Connect**: On session connection to the websocket, the function for this route is called. Within the frontend, this route is followed by the setUsername function call.
- **setUsername**: After connecting to the websocket, this function is called via the setUsername action route which assigns a username to the connectionID and stores this value in the DynamoDB relational table utilized by this lambda function. 
- **Disconnect**: On session end, this function is called which deletes the connectID data and name from the DynamoDB table. 
- **sendPublicMsg**: This function is used to compile and broadcast messages from one user to all the others, a one-to-many broadcast. 

## Contact
Samuel Johnson - samj944@gmail.com  

