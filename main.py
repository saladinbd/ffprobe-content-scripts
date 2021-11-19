#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple
import json


class FFProbeResult(NamedTuple):
    return_code: int
    json: str
    error: str


def ffprobe(file_path) -> FFProbeResult:
    command_array = [
                        "ffprobe",
                        # "-v", "quiet",
                        "-print_format", "json",
                        # "-show_format",
                        # "-show_streams",
                        "-show_frames",
                        file_path
                    ]
    result = subprocess.run(command_array, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return FFProbeResult(return_code=result.returncode,
                         json=result.stdout,
                         error=result.stderr)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='View ffprobe output')
    parser.add_argument('-i', '--input', help='File Name', required=True)
    args = parser.parse_args()
    if not Path(args.input).is_file():
        print("could not read file: " + args.input)
        exit(1)
    print('File:       {}'.format(args.input))
    ffprobe_result = ffprobe(file_path=args.input)
    if ffprobe_result.return_code == 0:
        # Print the raw json string
        # print(ffprobe_result.json)

        d = json.loads(ffprobe_result.json)
        frames = d.get("frames", [])
        total_audio_duration = 0.0
        total_video_duration = 0.0
        sum_video = {}
        sum_audio = {}
        for frame in frames:
            # print(frame)
            if frame.get("media_type") == "audio":
                if frame.get("stream_index") not in sum_audio:
                    sum_audio[frame.get("stream_index")] = 0.0
                sum_audio[frame.get("stream_index")] += float(frame.get("pkt_duration_time", 0.0))
            elif frame.get("media_type") == "video":
                if frame.get("stream_index") not in sum_video:
                    sum_video[frame.get("stream_index")] = 0.0
                sum_video[frame.get("stream_index")] += float(frame.get("pkt_duration_time", 0.0))
                

        # or print a summary of each stream
        # d = json.loads(ffprobe_result.json)
        # streams = d.get("streams", [])
        # for stream in streams:
        #     print("------------ showing streams -----------------")
        #     print(f'{stream.get("codec_type", "unknown")}: {stream.get("codec_long_name")}')

        print(f"audio duration: {sum_audio} | video duration: {sum_video}")

    else:
        print("ERROR")
        print(ffprobe_result.error, file=sys.stderr)