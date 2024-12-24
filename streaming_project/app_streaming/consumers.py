# import json
# import logging
# import gc
# from channels.generic.websocket import AsyncWebsocketConsumer
# from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
# from aiortc.contrib.media import MediaPlayer

# logger = logging.getLogger(__name__)
# # daphne -b 127.0.0.1 -p 8000 streaming_project.asgi:application
# # Define your RTSP streams here
# RTSP_STREAMS = [
    
#     "rtsp://172.16.12.28:8554/live1.sdp",
#     "rtsp://172.16.12.28:8554/live2.sdp",
#     "rtsp://172.16.12.28:8554/live3.sdp",
#     "rtsp://172.16.12.28:8554/live4.sdp",
#     "rtsp://172.16.12.28:8554/live5.sdp",

#     "rtsp://172.16.12.28:8554/live1.sdp",
#     "rtsp://172.16.12.28:8554/live2.sdp",
#     "rtsp://172.16.12.28:8554/live3.sdp",
#     "rtsp://172.16.12.28:8554/live4.sdp",
#     "rtsp://172.16.12.28:8554/live5.sdp",

#     "rtsp://172.16.12.28:8554/live1.sdp",
#     "rtsp://172.16.12.28:8554/live2.sdp",
#     "rtsp://172.16.12.28:8554/live3.sdp",
#     "rtsp://172.16.12.28:8554/live4.sdp",
#     "rtsp://172.16.12.28:8554/live5.sdp",

#     "rtsp://172.16.12.28:8554/live1.sdp",
#     "rtsp://172.16.12.28:8554/live2.sdp",
#     "rtsp://172.16.12.28:8554/live3.sdp",
#     "rtsp://172.16.12.28:8554/live4.sdp",
#     "rtsp://172.16.12.28:8554/live5.sdp",
   
#     "rtsp://172.16.12.28:8554/live1.sdp",
#     "rtsp://172.16.12.28:8554/live2.sdp",
#     "rtsp://172.16.12.28:8554/live3.sdp",
#     "rtsp://172.16.12.28:8554/live4.sdp",
#     "rtsp://172.16.12.28:8554/live5.sdp",

#     "rtsp://172.16.12.28:8554/live1.sdp",
#     "rtsp://172.16.12.28:8554/live2.sdp",
#     "rtsp://172.16.12.28:8554/live3.sdp",
#     "rtsp://172.16.12.28:8554/live4.sdp",
#     "rtsp://172.16.12.28:8554/live5.sdp",

# ]

# class WebRTCConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         logger.info("WebSocket connection established.")
#         self.pcs = {}
#         self.players = {}
#         self.active_streams = set()
#         await self.accept()
#         await self.send(json.dumps({    
#             'type': 'stream_count',
#             'count': len(RTSP_STREAMS)
#         }))

#     async def receive(self, text_data):
#         logger.info(f"Received message: {text_data}")
#         try:
#             message = json.loads(text_data)
#             stream_id = message.get('streamId')

#             if message['type'] == 'request_stream':
#                 logger.info(f"Stream requested: {stream_id}")
#                 if stream_id is not None and 0 <= stream_id < len(RTSP_STREAMS):
#                     await self.start_stream(stream_id)
#                 else:
#                     await self.send(json.dumps({'type': 'error', 'message': 'Invalid stream ID'}))

#             elif message['type'] == 'offer':
#                 await self.handle_offer(message, stream_id)

#             elif message['type'] == 'ice':
#                 await self.handle_ice_candidate(message, stream_id)

#         except Exception as e:
#             logger.error(f"Error in WebRTC consumer: {e}")
#             if 'stream_id' in locals() and stream_id is not None:
#                 await self.cleanup_stream(stream_id)

#     async def handle_offer(self, message, stream_id):
#         await self.cleanup_stream(stream_id)

#         # Create RTCConfiguration with RTCIceServer
#         config = RTCConfiguration(
#             iceServers=[
#                 RTCIceServer(urls=['stun:stun.l.google.com:19302'])
#             ]
#         )

#         logger.debug("RTCConfiguration being used:")
#         pc = RTCPeerConnection(configuration=config)
#         self.pcs[stream_id] = pc

#         # Initialize MediaPlayer for the RTSP stream iit is only giving me only 1 stream and also 
#         self.players[stream_id] = MediaPlayer(
#             RTSP_STREAMS[stream_id],
#             options={
#                 'rtsp_transport': 'tcp',
#                 'fflags': 'nobuffer',
#                 'flags': 'low_delay',
#                 'probesize': '32',
#                 'analyzeduration': '0'
#             }
#         )

#         # Add video track
#         if self.players[stream_id].video:
#             logger.debug(f"Adding video track for stream {stream_id}")
#             pc.addTrack(self.players[stream_id].video)
#         else:
#             logger.error(f"No video track found for stream {stream_id}")

#         @pc.on('connectionstatechange')
#         async def on_connectionstatechange():
#             logger.info(f"Connection state for stream {stream_id}: {pc.connectionState}")
#             if pc.connectionState in ["failed", "closed"]:
#                 await self.cleanup_stream(stream_id)

#         try:
#             # Set remote description
#             await pc.setRemoteDescription(RTCSessionDescription(sdp=message['sdp'], type='offer'))
#             answer = await pc.createAnswer()
#             await pc.setLocalDescription(answer)

#             await self.send(json.dumps({
#                 'type': 'answer',
#                 'streamId': stream_id,
#                 'sdp': pc.localDescription.sdp
#             }))
#             logger.info(f"Sent answer for stream {stream_id}")

#         except Exception as e:
#             logger.error(f"Error during offer handling: {e}")
#             await self.cleanup_stream(stream_id)

#     async def handle_ice_candidate(self, message, stream_id):
#         if stream_id in self.pcs:
#             pc = self.pcs[stream_id]
#             candidate = message.get('candidate')
#             if candidate:
#                 try:
#                     # Add the ICE candidate from the client
#                     await pc.addIceCandidate(candidate)
#                     logger.debug(f"Added ICE candidate for stream {stream_id}")
#                 except Exception as e:
#                     logger.error(f"Error adding ICE candidate: {e}")

#     async def cleanup_stream(self, stream_id):
#         logger.info(f"Cleaning up stream: {stream_id}")
#         try:
#             if stream_id in self.pcs:
#                 await self.pcs[stream_id].close()
#                 del self.pcs[stream_id]
#                 logger.debug(f"Closed RTCPeerConnection for stream {stream_id}")

#             if stream_id in self.players:
#                 player = self.players[stream_id]
#                 if player.video:
#                     player.video.stop()
#                 if player.audio:
#                     player.audio.stop()
#                 del self.players[stream_id]
#                 logger.debug(f"Stopped MediaPlayer for stream {stream_id}")

#             self.active_streams.discard(stream_id)
#             logger.debug(f"Removed stream {stream_id} from active streams")
#         except Exception as e:
#             logger.error(f"Error during cleanup: {e}")
#         finally:
#             gc.collect()

#     async def disconnect(self, close_code):
#         logger.info("WebSocket connection closed.")
#         for s_id in list(self.pcs.keys()):
#             await self.cleanup_stream(s_id)

#     async def start_stream(self, stream_id):
#         logger.info(f"Starting stream for ID: {stream_id}")
#         try:
#             await self.send(json.dumps({'type': 'offer_needed', 'streamId': stream_id}))
#             logger.debug(f"Sent offer_needed for stream {stream_id}")
#         except Exception as e:
#             logger.error(f"Error starting stream: {e}")



# proper working at 10 fps

# import json
# import logging
# import gc
# import asyncio

# from channels.generic.websocket import AsyncWebsocketConsumer
# from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
# from aiortc.contrib.media import MediaPlayer

# logger = logging.getLogger(__name__)

# # Example RTSP streams (replace with your actual URLs):
# RTSP_STREAMS = [
#     "rtsp://172.16.12.28:8554/live1.sdp",
#     "rtsp://172.16.12.28:8554/live2.sdp",
#     "rtsp://172.16.12.28:8554/live3.sdp",
#     "rtsp://172.16.12.28:8554/live4.sdp",
#     "rtsp://172.16.12.28:8554/live5.sdp",
#     "rtsp://172.16.12.28:8554/live1.sdp",
#     "rtsp://172.16.12.28:8554/live2.sdp",
#     "rtsp://172.16.12.28:8554/live3.sdp",
#     "rtsp://172.16.12.28:8554/live4.sdp",
#     "rtsp://172.16.12.28:8554/live5.sdp",

#     "rtsp://172.16.12.28:8554/live1.sdp",
#     "rtsp://172.16.12.28:8554/live2.sdp",
#     "rtsp://172.16.12.28:8554/live3.sdp",
#     "rtsp://172.16.12.28:8554/live4.sdp",
#     "rtsp://172.16.12.28:8554/live5.sdp",
#     "rtsp://172.16.12.28:8554/live1.sdp",
#     "rtsp://172.16.12.28:8554/live2.sdp",
#     "rtsp://172.16.12.28:8554/live3.sdp",
#     "rtsp://172.16.12.28:8554/live4.sdp",
#     "rtsp://172.16.12.28:8554/live5.sdp",
   
#     "rtsp://172.16.12.28:8554/live1.sdp",
#     "rtsp://172.16.12.28:8554/live2.sdp",
#     "rtsp://172.16.12.28:8554/live3.sdp",
#     "rtsp://172.16.12.28:8554/live4.sdp",
#     "rtsp://172.16.12.28:8554/live5.sdp",
#     "rtsp://172.16.12.28:8554/live1.sdp",
#     "rtsp://172.16.12.28:8554/live2.sdp",
#     "rtsp://172.16.12.28:8554/live3.sdp",
#     "rtsp://172.16.12.28:8554/live4.sdp",
#     "rtsp://172.16.12.28:8554/live5.sdp",


#     "rtsp://172.16.12.28:8554/live1.sdp",
#     "rtsp://172.16.12.28:8554/live2.sdp",
#     "rtsp://172.16.12.28:8554/live3.sdp",
#     "rtsp://172.16.12.28:8554/live4.sdp",
#     "rtsp://172.16.12.28:8554/live5.sdp",
#     "rtsp://172.16.12.28:8554/live1.sdp",
#     "rtsp://172.16.12.28:8554/live2.sdp",
#     "rtsp://172.16.12.28:8554/live3.sdp",
#     "rtsp://172.16.12.28:8554/live4.sdp",
#     "rtsp://172.16.12.28:8554/live5.sdp",


#     # "rtsp://172.16.12.28:8554/live1.sdp",
#     # "rtsp://172.16.12.28:8554/live2.sdp",
#     # "rtsp://172.16.12.28:8554/live3.sdp",
#     # "rtsp://172.16.12.28:8554/live4.sdp",
#     # "rtsp://172.16.12.28:8554/live5.sdp",
#     # "rtsp://172.16.12.28:8554/live1.sdp",
#     # "rtsp://172.16.12.28:8554/live2.sdp",
#     # "rtsp://172.16.12.28:8554/live3.sdp",
#     # "rtsp://172.16.12.28:8554/live4.sdp",
#     # "rtsp://172.16.12.28:8554/live5.sdp",


#     # "rtsp://172.16.12.28:8554/live1.sdp",
#     # "rtsp://172.16.12.28:8554/live2.sdp",
#     # "rtsp://172.16.12.28:8554/live3.sdp",
#     # "rtsp://172.16.12.28:8554/live4.sdp",
#     # "rtsp://172.16.12.28:8554/live5.sdp",
#     # "rtsp://172.16.12.28:8554/live1.sdp",
#     # "rtsp://172.16.12.28:8554/live2.sdp",
#     # "rtsp://172.16.12.28:8554/live3.sdp",
#     # "rtsp://172.16.12.28:8554/live4.sdp",
#     # "rtsp://172.16.12.28:8554/live5.sdp",


#     # "rtsp://172.16.12.28:8554/live1.sdp",
#     # "rtsp://172.16.12.28:8554/live2.sdp",
#     # "rtsp://172.16.12.28:8554/live3.sdp",
#     # "rtsp://172.16.12.28:8554/live4.sdp",
    
# ]

# class WebRTCConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         logger.info("WebSocket connection established.")
#         self.pcs = {}            # Holds RTCPeerConnection objects
#         self.players = {}        # Holds MediaPlayer objects
#         self.active_streams = set()
#         await self.accept()

#         # Let the client know how many RTSP streams exist
#         await self.send(json.dumps({
#             'type': 'stream_count',
#             'count': len(RTSP_STREAMS)
#         }))

#     async def receive(self, text_data):
#         logger.info(f"Received message: {text_data}")
#         try:
#             message = json.loads(text_data)
#             stream_id = message.get('streamId')

#             if message['type'] == 'request_stream':
#                 logger.info(f"Stream requested: {stream_id}")
#                 if stream_id is not None and 0 <= stream_id < len(RTSP_STREAMS):
#                     await self.start_stream(stream_id)
#                 else:
#                     await self.send(json.dumps({
#                         'type': 'error',
#                         'message': 'Invalid stream ID'
#                     }))

#             elif message['type'] == 'offer':
#                 await self.handle_offer(message, stream_id)

#             elif message['type'] == 'ice':
#                 await self.handle_ice_candidate(message, stream_id)

#         except Exception as e:
#             logger.error(f"Error in WebRTC consumer: {e}")
#             if 'stream_id' in locals() and stream_id is not None:
#                 await self.cleanup_stream(stream_id)

#     async def handle_offer(self, message, stream_id):
#         # First cleanup any existing PC or MediaPlayer for this stream
#         await self.cleanup_stream(stream_id)

#         # Example RTC config with STUN (and optional TURN if needed):
#         # If you have a TURN server, uncomment the lines below.
#         # turn_server = RTCIceServer(
#         #     urls=["turn:your-turn-server:3478"],
#         #     username="user",
#         #     credential="pass"
#         # )
#         config = RTCConfiguration(
#             iceServers=[
#                 RTCIceServer(urls=['stun:stun.l.google.com:19302']),
#                 # turn_server  # Uncomment if you actually have TURN server credentials
#             ]
#         )

#         logger.debug("RTCConfiguration being used: %s", config)
#         pc = RTCPeerConnection(configuration=config)
#         self.pcs[stream_id] = pc

#         # Create the MediaPlayer with extended RTSP options
#         # 'stimeout' can help if a stream stalls or if you want to keep the session alive
#         self.players[stream_id] = MediaPlayer(
#             RTSP_STREAMS[stream_id],
#             options={
#                 'rtsp_transport': 'tcp',
#                 # 'stimeout': '5000000',  # 5-second read-timeout in microseconds
#                 'fflags': 'nobuffer',
#                 'flags': 'low_delay',
#                 'probesize': '32',
#                 'analyzeduration': '0'
#             }
#         )

#         # Add video track if available
#         if self.players[stream_id].video:
#             logger.debug(f"Adding video track for stream {stream_id}")
#             pc.addTrack(self.players[stream_id].video)
#         else:
#             logger.error(f"No video track found for stream {stream_id}")

#         @pc.on('connectionstatechange')
#         async def on_connectionstatechange():
#             logger.info(f"Connection state for stream {stream_id}: {pc.connectionState}")
#             # If the connection fails or closes, we attempt a reconnect
#             if pc.connectionState in ["failed", "closed", "disconnected"]:
#                 # Clean up
#                 await self.cleanup_stream(stream_id)
#                 # Optionally wait a bit before reconnecting
#                 await asyncio.sleep(1)
#                 # Attempt to start the stream again
#                 await self.start_stream(stream_id)

#         try:
#             # Set remote description from the client's offer
#             await pc.setRemoteDescription(RTCSessionDescription(
#                 sdp=message['sdp'],
#                 type='offer'
#             ))

#             # Create and set our answer
#             answer = await pc.createAnswer()
#             await pc.setLocalDescription(answer)

#             # Send the answer back
#             await self.send(json.dumps({
#                 'type': 'answer',
#                 'streamId': stream_id,
#                 'sdp': pc.localDescription.sdp
#             }))
#             logger.info(f"Sent answer for stream {stream_id}")

#         except Exception as e:
#             logger.error(f"Error during offer handling: {e}")
#             await self.cleanup_stream(stream_id)

#     async def handle_ice_candidate(self, message, stream_id):
#         # Called when the client sends an ICE candidate
#         if stream_id in self.pcs:
#             pc = self.pcs[stream_id]
#             candidate = message.get('candidate')
#             if candidate:
#                 try:
#                     await pc.addIceCandidate(candidate)
#                     logger.debug(f"Added ICE candidate for stream {stream_id}")
#                 except Exception as e:
#                     logger.error(f"Error adding ICE candidate: {e}")

#     async def cleanup_stream(self, stream_id):
#         logger.info(f"Cleaning up stream: {stream_id}")
#         try:
#             # Close and remove the RTCPeerConnection
#             if stream_id in self.pcs:
#                 await self.pcs[stream_id].close()
#                 del self.pcs[stream_id]
#                 logger.debug(f"Closed RTCPeerConnection for stream {stream_id}")

#             # Stop and remove the MediaPlayer
#             if stream_id in self.players:
#                 player = self.players[stream_id]
#                 if player.video:
#                     player.video.stop()
#                 if player.audio:
#                     player.audio.stop()
#                 del self.players[stream_id]
#                 logger.debug(f"Stopped MediaPlayer for stream {stream_id}")

#             # Remove from active streams set
#             self.active_streams.discard(stream_id)
#             logger.debug(f"Removed stream {stream_id} from active streams")

#         except Exception as e:
#             logger.error(f"Error during cleanup: {e}")
#         finally:
#             gc.collect()

#     async def disconnect(self, close_code):
#         logger.info("WebSocket connection closed.")
#         # Clean up all active streams
#         for s_id in list(self.pcs.keys()):
#             await self.cleanup_stream(s_id)

#     async def start_stream(self, stream_id):
#         logger.info(f"Starting stream for ID: {stream_id}")
#         try:
#             # Ask the client to send an offer
#             await self.send(json.dumps({'type': 'offer_needed', 'streamId': stream_id}))
#             logger.debug(f"Sent offer_needed for stream {stream_id}")
#         except Exception as e:
#             logger.error(f"Error starting stream: {e}")



import json
import logging
import gc
import asyncio

from channels.generic.websocket import AsyncWebsocketConsumer
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaPlayer

logger = logging.getLogger(__name__)

# Define your RTSP streams here (ensure uniqueness or reuse MediaPlayers if possible)
RTSP_STREAMS = [
       "rtsp://172.16.12.28:8554/live1.sdp",
    "rtsp://172.16.12.28:8554/live2.sdp",
    "rtsp://172.16.12.28:8554/live3.sdp",
    "rtsp://172.16.12.28:8554/live4.sdp",
    "rtsp://172.16.12.28:8554/live5.sdp",
    "rtsp://172.16.12.28:8554/live1.sdp",
    "rtsp://172.16.12.28:8554/live2.sdp",
    "rtsp://172.16.12.28:8554/live3.sdp",
    "rtsp://172.16.12.28:8554/live4.sdp",
    "rtsp://172.16.12.28:8554/live5.sdp",

    "rtsp://172.16.12.28:8554/live1.sdp",
    "rtsp://172.16.12.28:8554/live2.sdp",
    "rtsp://172.16.12.28:8554/live3.sdp",
    "rtsp://172.16.12.28:8554/live4.sdp",
    "rtsp://172.16.12.28:8554/live5.sdp",
    "rtsp://172.16.12.28:8554/live1.sdp",
    "rtsp://172.16.12.28:8554/live2.sdp",
    "rtsp://172.16.12.28:8554/live3.sdp",
    "rtsp://172.16.12.28:8554/live4.sdp",
    "rtsp://172.16.12.28:8554/live5.sdp",
   
    "rtsp://172.16.12.28:8554/live1.sdp",
    "rtsp://172.16.12.28:8554/live2.sdp",
    "rtsp://172.16.12.28:8554/live3.sdp",
    "rtsp://172.16.12.28:8554/live4.sdp",
    "rtsp://172.16.12.28:8554/live5.sdp",
    "rtsp://172.16.12.28:8554/live1.sdp",
    "rtsp://172.16.12.28:8554/live2.sdp",
    "rtsp://172.16.12.28:8554/live3.sdp",
    "rtsp://172.16.12.28:8554/live4.sdp",
    "rtsp://172.16.12.28:8554/live5.sdp",


    "rtsp://172.16.12.28:8554/live1.sdp",
    "rtsp://172.16.12.28:8554/live2.sdp",
    "rtsp://172.16.12.28:8554/live3.sdp",
    "rtsp://172.16.12.28:8554/live4.sdp",
    "rtsp://172.16.12.28:8554/live5.sdp",
    "rtsp://172.16.12.28:8554/live1.sdp",
    "rtsp://172.16.12.28:8554/live2.sdp",
    "rtsp://172.16.12.28:8554/live3.sdp",
    "rtsp://172.16.12.28:8554/live4.sdp",
    "rtsp://172.16.12.28:8554/live5.sdp",


    # "rtsp://172.16.12.28:8554/live1.sdp",
    # "rtsp://172.16.12.28:8554/live2.sdp",
    # "rtsp://172.16.12.28:8554/live3.sdp",
    # "rtsp://172.16.12.28:8554/live4.sdp",
    # "rtsp://172.16.12.28:8554/live5.sdp",
    # "rtsp://172.16.12.28:8554/live1.sdp",
    # "rtsp://172.16.12.28:8554/live2.sdp",
    # "rtsp://172.16.12.28:8554/live3.sdp",
    # "rtsp://172.16.12.28:8554/live4.sdp",
    # "rtsp://172.16.12.28:8554/live5.sdp",


    # "rtsp://172.16.12.28:8554/live1.sdp",
    # "rtsp://172.16.12.28:8554/live2.sdp",
    # "rtsp://172.16.12.28:8554/live3.sdp",
    # "rtsp://172.16.12.28:8554/live4.sdp",
    # "rtsp://172.16.12.28:8554/live5.sdp",
    # "rtsp://172.16.12.28:8554/live1.sdp",
    # "rtsp://172.16.12.28:8554/live2.sdp",
    # "rtsp://172.16.12.28:8554/live3.sdp",
    # "rtsp://172.16.12.28:8554/live4.sdp",
    # "rtsp://172.16.12.28:8554/live5.sdp",


    # "rtsp://172.16.12.28:8554/live1.sdp",
    # "rtsp://172.16.12.28:8554/live2.sdp",
    # "rtsp://172.16.12.28:8554/live3.sdp",
    # "rtsp://172.16.12.28:8554/live4.sdp",
]

class WebRTCConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info("WebSocket connection established.")
        self.pcs = {}            # Holds RTCPeerConnection objects
        self.players = {}        # Holds MediaPlayer objects
        self.active_streams = set()
        await self.accept()

        # Let the client know how many RTSP streams exist
        await self.send(json.dumps({
            'type': 'stream_count',
            'count': len(RTSP_STREAMS)
        }))

    async def receive(self, text_data):
        logger.debug(f"Received message: {text_data}")
        try:
            message = json.loads(text_data)
            stream_id = message.get('streamId')

            if message['type'] == 'request_stream':
                logger.info(f"Stream requested: {stream_id}")
                if stream_id is not None and 0 <= stream_id < len(RTSP_STREAMS):
                    asyncio.create_task(self.start_stream(stream_id))
                else:
                    await self.send(json.dumps({
                        'type': 'error',
                        'message': 'Invalid stream ID'
                    }))

            elif message['type'] == 'offer':
                asyncio.create_task(self.handle_offer(message, stream_id))

            elif message['type'] == 'ice':
                asyncio.create_task(self.handle_ice_candidate(message, stream_id))

        except Exception as e:
            logger.error(f"Error in WebRTC consumer: {e}")
            if 'stream_id' in locals() and stream_id is not None:
                asyncio.create_task(self.cleanup_stream(stream_id))

    async def handle_offer(self, message, stream_id):
        # First cleanup any existing PC or MediaPlayer for this stream
        await self.cleanup_stream(stream_id)

        # Example RTC config with STUN (and optional TURN if needed)
        # If you have a TURN server, uncomment the lines below.
        # turn_server = RTCIceServer(
        #     urls=["turn:your-turn-server:3478"],
        #     username="user",
        #     credential="pass"
        # )
        config = RTCConfiguration(
            iceServers=[
                RTCIceServer(urls=['stun:stun.l.google.com:19302']),
                # turn_server  # Uncomment if you actually have TURN server credentials
            ]
        )

        logger.debug("RTCConfiguration being used: %s", config)
        pc = RTCPeerConnection(configuration=config)
        self.pcs[stream_id] = pc

        # Create the MediaPlayer with extended RTSP options
        # 'stimeout' can help if a stream stalls or if you want to keep the session alive
        self.players[stream_id] = MediaPlayer(
            RTSP_STREAMS[stream_id],
            options={
                'rtsp_transport': 'tcp',
                'fflags': 'nobuffer',
                'flags': 'low_delay',
                'probesize': '32',
                'analyzeduration': '0',
                # 'stimeout': '5000000',  # Uncomment if supported and necessary
            }
        )

        # Add video track if available
        if self.players[stream_id].video:
            logger.debug(f"Adding video track for stream {stream_id}")
            pc.addTrack(self.players[stream_id].video)
        else:
            logger.error(f"No video track found for stream {stream_id}")

        @pc.on('connectionstatechange')
        async def on_connectionstatechange():
            logger.info(f"Connection state for stream {stream_id}: {pc.connectionState}")
            # If the connection fails or closes, attempt a reconnect
            if pc.connectionState in ["failed", "closed", "disconnected"]:
                await self.cleanup_stream(stream_id)
                # Optionally wait a bit before reconnecting
                await asyncio.sleep(1)
                # Attempt to start the stream again
                await self.start_stream(stream_id)

        try:
            # Set remote description from the client's offer
            await pc.setRemoteDescription(RTCSessionDescription(
                sdp=message['sdp'],
                type='offer'
            ))

            # Create and set our answer
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)

            # Send the answer back
            await self.send(json.dumps({
                'type': 'answer',
                'streamId': stream_id,
                'sdp': pc.localDescription.sdp
            }))
            logger.info(f"Sent answer for stream {stream_id}")

        except Exception as e:
            logger.error(f"Error during offer handling: {e}")
            await self.cleanup_stream(stream_id)

    async def handle_ice_candidate(self, message, stream_id):
        # Called when the client sends an ICE candidate
        if stream_id in self.pcs:
            pc = self.pcs[stream_id]
            candidate = message.get('candidate')
            if candidate:
                try:
                    await pc.addIceCandidate(candidate)
                    logger.debug(f"Added ICE candidate for stream {stream_id}")
                except Exception as e:
                    logger.error(f"Error adding ICE candidate: {e}")

    async def cleanup_stream(self, stream_id):
        logger.info(f"Cleaning up stream: {stream_id}")
        try:
            # Close and remove the RTCPeerConnection
            if stream_id in self.pcs:
                await self.pcs[stream_id].close()
                del self.pcs[stream_id]
                logger.debug(f"Closed RTCPeerConnection for stream {stream_id}")

            # Stop and remove the MediaPlayer
            if stream_id in self.players:
                player = self.players[stream_id]
                if player.video:
                    player.video.stop()
                if player.audio:
                    player.audio.stop()
                del self.players[stream_id]
                logger.debug(f"Stopped MediaPlayer for stream {stream_id}")

            # Remove from active streams set
            self.active_streams.discard(stream_id)
            logger.debug(f"Removed stream {stream_id} from active streams")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        finally:
            gc.collect()

    async def disconnect(self, close_code):
        logger.info("WebSocket connection closed.")
        # Clean up all active streams
        for s_id in list(self.pcs.keys()):
            await self.cleanup_stream(s_id)

    async def start_stream(self, stream_id):
        logger.info(f"Starting stream for ID: {stream_id}")
        try:
            # Ask the client to send an offer
            await self.send(json.dumps({'type': 'offer_needed', 'streamId': stream_id}))
            logger.debug(f"Sent offer_needed for stream {stream_id}")
        except Exception as e:
            logger.error(f"Error starting stream: {e}")
