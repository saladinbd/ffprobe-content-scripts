#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple
import json
import logging

logging.root.handlers = []
logging.basicConfig(format='%(asctime)s - %(name)s:%(lineno)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class FFProbeResult(NamedTuple):
    return_code: int
    return_format: str
    result: str
    error: str


def ffprobe(file_path, print_format="json") -> FFProbeResult:
    command_array = [
                        "ffprobe",
                        "-print_format", print_format,
                        "-show_streams",
                        "-show_frames",
                        file_path
                    ]

    result = subprocess.run(command_array, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    return FFProbeResult(return_code=result.returncode,
                         result=result.stdout,
                         return_format=print_format,
                         error=result.stderr)

def calculate_duration(content_frames):
    frames = content_frames.get("frames", [])

    sum_video = {}
    sum_audio = {}
    for frame in frames:

        if frame.get("media_type") == "audio":
            if frame.get("stream_index") not in sum_audio:
                sum_audio[frame.get("stream_index")] = 0.0
            sum_audio[frame.get("stream_index")] += float(frame.get("pkt_duration_time", 0.0))

        elif frame.get("media_type") == "video":
            if frame.get("stream_index") not in sum_video:
                sum_video[frame.get("stream_index")] = 0.0
            sum_video[frame.get("stream_index")] += float(frame.get("pkt_duration_time", 0.0))

    return {
        "audio_frames_total_duration": list(sum_audio.values()),
        "video_frames_total_duration": list(sum_video.values())
    }


def validate_audio_video_frames_duration(content_metadata):
    
    video_duration = content_metadata.get("video_frames_total_duration")[0]

    if round(video_duration, 2) % 1.92 != 0.0:
        logger.exception(f"total frame duration not divisible by 1.92 [{video_duration}]")
        return False

    for duration in content_metadata.get("audio_frames_total_duration"):
        if video_duration != duration:
            logger.exception(f"Video and Audio duration not sync [{video_duration}, {duration}]")
            return False

    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='View ffprobe output')
    parser.add_argument('-i', '--input', help='File Name', required=True)
    parser.add_argument('-frm', '--return_format', help='CSV|JSON', required=True)
    args = parser.parse_args()
    if not Path(args.input).is_file():
        logger.exception(f"could not read file: {args.input}")
        exit(1)
    logger.info('File: {}'.format(args.input))
    ffprobe_result = ffprobe(file_path=args.input, print_format=args.return_format)

    if ffprobe_result.return_code == 0:
        
        data = json.loads(ffprobe_result.result)

        file_name = args.input.split(".")[0]
        with open(f"{file_name}.json", 'w+') as outfile:
            json.dump(data, outfile, sort_keys=True, indent=4)

        result = calculate_duration(data)
        logger.info(f"calculation result {result}")

        if validate_audio_video_frames_duration(result):
            logger.info(f"content is valid: {args.input}")

    else:
        logger.exception(ffprobe_result.error, file=sys.stderr)