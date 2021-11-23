#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple
import json


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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='View ffprobe output')
    parser.add_argument('-i', '--input', help='File Name', required=True)
    parser.add_argument('-frm', '--return_format', help='CSV|JSON', required=True)
    args = parser.parse_args()
    if not Path(args.input).is_file():
        print("could not read file: " + args.input)
        exit(1)
    print('File:       {}'.format(args.input))
    ffprobe_result = ffprobe(file_path=args.input, print_format=args.return_format)
    print(ffprobe_result.return_code)
    if ffprobe_result.return_code == 0:
        

        file_name = args.input.split(".")[0]
        data = json.loads(ffprobe_result.result)
        with open(f"{file_name}.json", 'w+') as outfile:
            json.dump(data, outfile, sort_keys=True, indent=4)

        frames = data.get("frames", [])

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


        print(f"audio duration: {sum_audio} | video duration: {sum_video}")

    else:
        print("ERROR")
        print(ffprobe_result.error, file=sys.stderr)