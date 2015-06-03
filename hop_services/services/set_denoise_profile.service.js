/* @bug Sometimes the websocket implementation from hop gets undefined before
 * the onmessage event calls
 */

hop = require('hop');
fs = require('fs');

var user = process.env.LOGNAME;
var storePath = "/home/" + user + "/hop_temps/"; 

/*----<Load modules used by the service>----*/
var rosService = "/ric/audio_processing/set_noise_profile";
var randStringGen = require('../utilities/./randStringGen.js');

/*----<Random String Generator configurations---->*/
var stringLength = 5;
var randStrGen = new randStringGen( stringLength );
/*------------------------------------------------*/


service set_denoise_profile( {noise_audio_fileUri:'', audio_file_type:'', user:''}  )
{
  /* --< Perform renaming on the reived file. Add uniqueId value> --- */
  var unqExt = randStrGen.createUnique();
  randStrGen.removeCached(unqExt);
  var file = noise_audio_fileUri.split('.');
  var fileUri_new = file[0] + '.' + file[1] +  unqExt + '.' + file[2]
    fs.renameSync(noise_audio_fileUri, fileUri_new);
  /*----------------------------------------------------------------- */
  return hop.HTTPResponseAsync(
    function( sendResponse ) 
    { 
      // sendResponse is a function argument that is generated by Hop to complete the service when the response is ready
      // here you need to send a message to rosbridge, prepare a callback to handle the result, and then  sendResponse( result ) in the callback body to actually return the service result.
      //var fileName = "speech-" + "bitch" + ".wav";
      //var audioFileUrl = Fs.resolvePath( storePath + fileName );
      //Fs.writeFileSync( audioFileUrl, fileData );
      var args = {
        'noise_audio_file': fileUri_new,
         'audio_file_type': audio_file_type,
         'user': user
      };

      var uniqueID = randStrGen.createUnique();
      var ros_srv_call = {
        'op': 'call_service',
         'service': rosService,
         'args': args,
         'id': uniqueID
      };

      var rosWS = new WebSocket('ws://localhost:9090');
      rosWS.onopen = function(){
        console.log('Connection to rosbridge established');
        this.send(JSON.stringify(ros_srv_call));
      };
      rosWS.onclose = function(){
        console.log('Connection to rosbridge closed');
      };
      rosWS.onmessage = function(event){
        console.log('Received message from rosbridge');
        var resp_msg = event.value;
        sendResponse( resp_msg );
        console.log(resp_msg);
        this.close();
        rosWS = undefined;
        randStrGen.removeCached( uniqueID );
      };

      function asyncWrap()
      {
        setTimeout( function()
        {
          if (respFlag != true)
          {
            console.log('Connection timed out! rosWs = undefined');
            if (rosWS != undefined)
            {
              rosWS.close();
            };
            rosWS = undefined;
            /* --< Re-open connection to the WebSocket >--*/
            rosWS = new WebSocket('ws://localhost:9090');
            /* -----------< Redefine WebSocket callbacks >----------- */
            rosWS.onopen = function(){
              console.log('Connection to rosbridge established');
              this.send(JSON.stringify(ros_srv_call));
            }
            rosWS.onclose = function(){
              console.log('Connection to rosbridge closed');
            }
            rosWS.onmessage = function(event){
              console.log('Received message from rosbridge');
              var resp_msg = event.value; 
              sendResponse( resp_msg ); //Return response to client
              console.log(resp_msg);
              this.close(); // Close the connection to the websocket
              rosWS = undefined; // Decostruct the websocket object
              respFlag = true;
              randStrGen.removeCached( uniqueID ); //Remove the uniqueID so it can be reused
            }
            /*--------------------------------------------------------*/
            asyncWrap();
          }
        }, 6000); //Timeout value is set at 10 seconds
      }
      asyncWrap();
    }, this ); // do not forget the <this> argument of hop.HTTResponseAsync 
}

