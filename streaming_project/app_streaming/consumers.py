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

#     "rtsp://172.16.12.33:8554/video1",
#     "rtsp://172.16.12.33:8554/video2",
#     "rtsp://172.16.12.33:8554/video3",
#     "rtsp://172.16.12.33:8554/video4",
#     "rtsp://172.16.12.33:8554/video5",
#     "rtsp://172.16.12.33:8554/video1",
#     "rtsp://172.16.12.33:8554/video2",
#     "rtsp://172.16.12.33:8554/video3",
#     "rtsp://172.16.12.33:8554/video4",
#     "rtsp://172.16.12.33:8554/video5",
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



#properly working but know it is start to stuck

# import json
# import logging
# import gc
# import asyncio
# from channels.generic.websocket import AsyncWebsocketConsumer
# from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
# from aiortc.contrib.media import MediaPlayer

# logger = logging.getLogger(__name__)

# RTSP_STREAMS = [   
#     "rtsp://172.16.12.28:8554/live1.sdp",
#     "rtsp://172.16.12.28:8554/live2.sdp",
#     "rtsp://172.16.12.28:8554/live3.sdp",
#     "rtsp://172.16.12.28:8554/live4.sdp",
#     "rtsp://172.16.12.28:8554/live5.sdp",
#     "rtsp://172.16.12.28:8554/live6.sdp",
#     "rtsp://172.16.12.28:8554/live7.sdp",
#     "rtsp://172.16.12.28:8554/live8.sdp",
#     "rtsp://172.16.12.28:8554/live9.sdp",
#     "rtsp://172.16.12.28:8554/live10.sdp",

# ]
# # daphne -b 0.0.0.0 -p 8000 streaming_project.asgi:application

# class WebRTCConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         logger.info("WebSocket connection established.")
#         self.pcs = {}
#         self.players = {}
#         self.active_streams = set()
#         await self.accept()

#         # Notify client about the number of available streams 
#         await self.send(json.dumps({
#             'type': 'stream_count',
#             'count': len(RTSP_STREAMS)
#         }))
#         logger.debug(f"Sent stream_count: {len(RTSP_STREAMS)}")

#     async def receive(self, text_data):
#         logger.debug(f"Received message: {text_data}")
#         try:
#             message = json.loads(text_data)
#             stream_id = message.get('streamId')

#             if message['type'] == 'request_stream':
#                 logger.info(f"Stream requested: {stream_id}")
#                 if stream_id is not None and 0 <= stream_id < len(RTSP_STREAMS):
#                     asyncio.create_task(self.start_stream(stream_id))
#                 else:
#                     await self.send(json.dumps({
#                         'type': 'error',
#                         'message': 'Invalid stream ID'
#                     }))
#                     logger.warning(f"Invalid stream ID received: {stream_id}")

#             elif message['type'] == 'offer':
#                 logger.info(f"Received offer for stream: {stream_id}")
#                 asyncio.create_task(self.handle_offer(message, stream_id))

#             elif message['type'] == 'ice':
#                 logger.info(f"Received ICE candidate for stream: {stream_id}")
#                 asyncio.create_task(self.handle_ice_candidate(message, stream_id))
                                                                
#             else:
#                 logger.warning(f"Unknown message type received: {message['type']}")

#         except json.JSONDecodeError as e:
#             logger.error(f"JSON decode error: {e}", exc_info=True)
#             await self.send(json.dumps({ 
#                 'type': 'error',
#                 'message': 'Invalid JSON format'
#             }))
#         except Exception as e:
#             logger.error(f"Unexpected error in receive: {e}", exc_info=True)
#             if 'stream_id' in locals() and stream_id is not None:
#                 asyncio.create_task(self.cleanup_stream(stream_id))

#     async def handle_offer(self, message, stream_id):
#         logger.debug(f"Handling offer for stream {stream_id}")
#         await self.cleanup_stream(stream_id)

#         config = RTCConfiguration(
#             iceServers=[
#                 RTCIceServer(urls=['stun:stun.l.google.com:19302']),
#                 # Add TURN servers if available   
#             ]
#         )

#         pc = RTCPeerConnection(configuration=config)
#         self.pcs[stream_id] = pc

#         try:
#             self.players[stream_id] = MediaPlayer(
#                 RTSP_STREAMS[stream_id],
#                 options={
#                     'rtsp_transport': 'tcp',
#                     'fflags': 'nobuffer',
#                     'flags': 'low_delay',
#                     'probesize': '5000',
#                     'analyzeduration': '5000000',
#                     'stimeout': '10000000',  # 10 seconds timeout
#                 }
#             )
#             logger.debug(f"Initialized MediaPlayer for stream {stream_id}")
#         except Exception as e:
#             logger.error(f"Failed to initialize MediaPlayer for stream {stream_id}: {e}", exc_info=True)
#             await self.send(json.dumps({
#                 'type': 'error',
#                 'message': f'Failed to initialize stream {stream_id}'
#             }))
#             await self.cleanup_stream(stream_id)
#             return

#         # Add video track if available
#         if self.players[stream_id].video:
#             logger.debug(f"Adding video track for stream {stream_id}")
#             pc.addTrack(self.players[stream_id].video)
#         else:
#             logger.error(f"No video track found for stream {stream_id}")
#             await self.send(json.dumps({
#                 'type': 'error',
#                 'message': f'No video track found for stream {stream_id}'
#             }))
#             await self.cleanup_stream(stream_id)
#             return

#         @pc.on('connectionstatechange')
#         async def on_connectionstatechange():
#             logger.info(f"Connection state for stream {stream_id}: {pc.connectionState}")
#             if pc.connectionState in ["failed", "closed", "disconnected"]:
#                 await self.cleanup_stream(stream_id)
#                 # Implement reconnection logic here if desired

#         try:
#             await pc.setRemoteDescription(RTCSessionDescription(
#                 sdp=message['sdp'],
#                 type='offer'
#             ))
#             logger.debug(f"Set remote description for stream {stream_id}")

#             answer = await pc.createAnswer()
#             await pc.setLocalDescription(answer)
#             logger.debug(f"Created and set local description for stream {stream_id}")

#             await self.send(json.dumps({
#                 'type': 'answer',
#                 'streamId': stream_id,
#                 'sdp': pc.localDescription.sdp
#             }))
#             logger.info(f"Sent answer for stream {stream_id}")

#         except Exception as e:
#             logger.error(f"Error during offer handling for stream {stream_id}: {e}", exc_info=True)
#             await self.cleanup_stream(stream_id)

#     async def handle_ice_candidate(self, message, stream_id):
#         logger.debug(f"Handling ICE candidate for stream {stream_id}")
#         if stream_id in self.pcs:
#             pc = self.pcs[stream_id]
#             candidate = message.get('candidate')
#             if candidate:
#                 try:
#                     await pc.addIceCandidate(candidate)
#                     logger.debug(f"Added ICE candidate for stream {stream_id}")
#                 except Exception as e:
#                     logger.error(f"Error adding ICE candidate for stream {stream_id}: {e}", exc_info=True)
#         else:
#             logger.warning(f"No RTCPeerConnection found for stream {stream_id}")

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
#                     logger.debug(f"Stopped video for stream {stream_id}")
#                 if player.audio:
#                     player.audio.stop()
#                     logger.debug(f"Stopped audio for stream {stream_id}")
#                 del self.players[stream_id]

#             self.active_streams.discard(stream_id)
#             logger.debug(f"Removed stream {stream_id} from active streams")

#         except Exception as e:
#             logger.error(f"Error during cleanup for stream {stream_id}: {e}", exc_info=True)
#         finally:
#             gc.collect()

#     async def disconnect(self, close_code):
#         logger.info("WebSocket connection closed.")
#         # Clean up all active streams 
#         for stream_id in list(self.pcs.keys()):
#             await self.cleanup_stream(stream_id)

#     async def start_stream(self, stream_id):
#         logger.info(f"Starting stream for ID: {stream_id}")
#         try:
#             await self.send(json.dumps({'type': 'offer_needed', 'streamId': stream_id}))
#             logger.debug(f"Sent 'offer_needed' for stream {stream_id}")
#         except Exception as e:
#             logger.error(f"Error starting stream {stream_id}: {e}", exc_info=True)

 


import json
import logging
import gc
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaPlayer

logger = logging.getLogger(__name__)

RTSP_STREAMS = [   
    "rtsp://172.16.12.33:8554/live1.sdp",
    "rtsp://172.16.12.33:8554/live2.sdp",
    "rtsp://172.16.12.33:8554/live3.sdp",
    "rtsp://172.16.12.33:8554/live4.sdp",
    "rtsp://172.16.12.33:8554/live5.sdp",
    "rtsp://172.16.12.33:8554/live6.sdp",
    "rtsp://172.16.12.33:8554/live7.sdp",
    "rtsp://172.16.12.33:8554/live8.sdp",
    "rtsp://172.16.12.33:8554/live9.sdp",
    "rtsp://172.16.12.33:8554/live10.sdp",
]

class WebRTCConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info("WebSocket connection established.")
        self.pcs = {}
        self.players = {}
        self.active_streams = set()
        self.stream_qualities = {}  # Track current quality per stream
        await self.accept()

        # Initialize stream qualities to default
        for stream_id in range(len(RTSP_STREAMS)):
            self.stream_qualities[stream_id] = 'default'

        # Notify client about the number of available streams 
        await self.send(json.dumps({
            'type': 'stream_count',
            'count': len(RTSP_STREAMS)
        }))
        logger.debug(f"Sent stream_count: {len(RTSP_STREAMS)}")

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
                    logger.warning(f"Invalid stream ID received: {stream_id}")

            elif message['type'] == 'offer':
                logger.info(f"Received offer for stream: {stream_id}")
                asyncio.create_task(self.handle_offer(message, stream_id))

            elif message['type'] == 'ice':
                logger.info(f"Received ICE candidate for stream: {stream_id}")
                asyncio.create_task(self.handle_ice_candidate(message, stream_id))
                
            elif message['type'] == 'increase_quality':
                logger.info(f"Received request to increase quality for stream: {stream_id}")
                asyncio.create_task(self.change_stream_quality(stream_id, 'high'))

            elif message['type'] == 'reset_quality':
                logger.info(f"Received request to reset quality for stream: {stream_id}")
                asyncio.create_task(self.change_stream_quality(stream_id, 'default'))

            else:
                logger.warning(f"Unknown message type received: {message['type']}")

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}", exc_info=True)
            await self.send(json.dumps({ 
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Unexpected error in receive: {e}", exc_info=True)
            if 'stream_id' in locals() and stream_id is not None:
                asyncio.create_task(self.cleanup_stream(stream_id))

    async def handle_offer(self, message, stream_id):
        logger.debug(f"Handling offer for stream {stream_id}")
        await self.cleanup_stream(stream_id)

        config = RTCConfiguration(
            iceServers=[
                RTCIceServer(urls=['stun:stun.l.google.com:19302']),
                # Add TURN servers if available   
            ]
        )

        pc = RTCPeerConnection(configuration=config)
        self.pcs[stream_id] = pc

        try:
            # Initialize MediaPlayer with current quality
            player = self.initialize_media_player(stream_id)
            self.players[stream_id] = player
            logger.debug(f"Initialized MediaPlayer for stream {stream_id} with quality {self.stream_qualities[stream_id]}")
        except Exception as e:
            logger.error(f"Failed to initialize MediaPlayer for stream {stream_id}: {e}", exc_info=True)
            await self.send(json.dumps({
                'type': 'error',
                'message': f'Failed to initialize stream {stream_id}'
            }))
            await self.cleanup_stream(stream_id)
            return

        # Add video track if available
        if self.players[stream_id].video:
            logger.debug(f"Adding video track for stream {stream_id}")
            pc.addTrack(self.players[stream_id].video)
        else:
            logger.error(f"No video track found for stream {stream_id}")
            await self.send(json.dumps({
                'type': 'error',
                'message': f'No video track found for stream {stream_id}'
            }))
            await self.cleanup_stream(stream_id)
            return

        @pc.on('connectionstatechange')
        async def on_connectionstatechange():
            logger.info(f"Connection state for stream {stream_id}: {pc.connectionState}")
            if pc.connectionState in ["failed", "closed", "disconnected"]:
                await self.cleanup_stream(stream_id)
                # Implement reconnection logic here if desired

        try:
            await pc.setRemoteDescription(RTCSessionDescription(
                sdp=message['sdp'],
                type='offer'
            ))
            logger.debug(f"Set remote description for stream {stream_id}")

            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            logger.debug(f"Created and set local description for stream {stream_id}")

            await self.send(json.dumps({
                'type': 'answer',
                'streamId': stream_id,
                'sdp': pc.localDescription.sdp
            }))
            logger.info(f"Sent answer for stream {stream_id}")

        except Exception as e:
            logger.error(f"Error during offer handling for stream {stream_id}: {e}", exc_info=True)
            await self.cleanup_stream(stream_id)

    def initialize_media_player(self, stream_id):
        """
        Initializes the MediaPlayer with the current quality settings.
        """
        quality = self.stream_qualities.get(stream_id, 'default')
        if quality == 'high':
            # High quality settings
            ffmpeg_command = [
                'ffmpeg',
                '-re',
                '-stream_loop', '-1',
                '-i', f'p{stream_id + 1}.mp4',
                '-filter:v', 'scale=1280:720,fps=30',  # Increased resolution and FPS
                '-c:v', 'libx264',
                '-preset', 'veryfast',
                '-crf', '23',
                '-b:v', '1M',  # Higher bitrate
                '-c:a', 'aac',
                '-b:a', '128k',
                '-f', 'rtsp',
                RTSP_STREAMS[stream_id]
            ]
        else:
            # Default quality settings
            ffmpeg_command = [
                'ffmpeg',
                '-re',
                '-stream_loop', '-1',
                '-i', f'p{stream_id + 1}.mp4',
                '-filter:v', 'scale=320x180,fps=10',  # Default resolution and FPS
                '-c:v', 'libx264',
                '-preset', 'veryfast',
                '-crf', '30',
                '-b:v', '300k',  # Default bitrate
                '-c:a', 'aac',
                '-b:a', '96k',
                '-f', 'rtsp',
                RTSP_STREAMS[stream_id]
            ]

        return MediaPlayer(
            RTSP_STREAMS[stream_id],
            options={
                'rtsp_transport': 'tcp',
                'fflags': 'nobuffer',
                'flags': 'low_delay',
                'probesize': '5000',
                'analyzeduration': '5000000',
                'stimeout': '10000000',  # 10 seconds timeout
            },
            run=ffmpeg_command
        )

    async def handle_ice_candidate(self, message, stream_id):
        logger.debug(f"Handling ICE candidate for stream {stream_id}")
        if stream_id in self.pcs:
            pc = self.pcs[stream_id]
            candidate = message.get('candidate')
            if candidate:
                try:
                    await pc.addIceCandidate(candidate)
                    logger.debug(f"Added ICE candidate for stream {stream_id}")
                except Exception as e:
                    logger.error(f"Error adding ICE candidate for stream {stream_id}: {e}", exc_info=True)
        else:
            logger.warning(f"No RTCPeerConnection found for stream {stream_id}")

    async def cleanup_stream(self, stream_id):
        logger.info(f"Cleaning up stream: {stream_id}")
        try:
            if stream_id in self.pcs:
                await self.pcs[stream_id].close()
                del self.pcs[stream_id]
                logger.debug(f"Closed RTCPeerConnection for stream {stream_id}")

            if stream_id in self.players:
                player = self.players[stream_id]
                if player.video:
                    player.video.stop()
                    logger.debug(f"Stopped video for stream {stream_id}")
                if player.audio:
                    player.audio.stop()
                    logger.debug(f"Stopped audio for stream {stream_id}")
                del self.players[stream_id]

            self.active_streams.discard(stream_id)
            logger.debug(f"Removed stream {stream_id} from active streams")

        except Exception as e:
            logger.error(f"Error during cleanup for stream {stream_id}: {e}", exc_info=True)
        finally:
            gc.collect()

    async def disconnect(self, close_code):
        logger.info("WebSocket connection closed.")
        # Clean up all active streams
        for stream_id in list(self.pcs.keys()):
            await self.cleanup_stream(stream_id)

    async def start_stream(self, stream_id):
        logger.info(f"Starting stream for ID: {stream_id}")
        try:
            await self.send(json.dumps({'type': 'offer_needed', 'streamId': stream_id}))
            logger.debug(f"Sent 'offer_needed' for stream {stream_id}")
        except Exception as e:
            logger.error(f"Error starting stream {stream_id}: {e}", exc_info=True)

    async def change_stream_quality(self, stream_id, quality):
        """
        Changes the quality of a specific stream by restarting the MediaPlayer with new parameters.
        """
        logger.info(f"Changing quality for stream {stream_id} to {quality}")
        try:
            # Update the quality state
            self.stream_qualities[stream_id] = quality

            # Cleanup existing stream
            await self.cleanup_stream(stream_id)

            # Initialize MediaPlayer with new quality
            player = self.initialize_media_player(stream_id)
            self.players[stream_id] = player
            logger.debug(f"Re-initialized MediaPlayer for stream {stream_id} with quality {quality}")

            # Re-establish the stream if it's currently connected
            if stream_id in self.pcs:
                # Close existing PeerConnection
                await self.pcs[stream_id].close()
                del self.pcs[stream_id]
                logger.debug(f"Closed existing PeerConnection for stream {stream_id}")

                # Notify frontend to renegotiate the connection
                await self.send(json.dumps({'type': 'offer_needed', 'streamId': stream_id}))
                logger.debug(f"Sent 'offer_needed' for stream {stream_id} after quality change")

            # Notify frontend that quality has changed
            await self.send(json.dumps({
                'type': 'quality_changed',
                'streamId': stream_id,
                'quality': quality
            }))
            logger.info(f"Quality changed for stream {stream_id} to {quality}")

        except Exception as e:
            logger.error(f"Error changing quality for stream {stream_id}: {e}", exc_info=True)
            await self.send(json.dumps({
                'type': 'error',
                'message': f'Failed to change quality for stream {stream_id}'
            }))
