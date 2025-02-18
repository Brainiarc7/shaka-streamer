#!/usr/bin/env python3
#
# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Shaka Streamer {version}

Shaka Streamer offers a simple config-file based approach to preparing streaming
media. It greatly simplifies the process of using FFmpeg and Shaka Packager for
both VOD and live content.
"""

import argparse
import os
import shutil
import time
import yaml

from streamer import VERSION
from streamer.controller_node import ControllerNode


class CustomArgParseFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter):
  """A custom argparse formatter that combines the features of multiple base
     classes.  This gives us defaults for each argument in the help text, plus
     it preserves whitespace in the description field."""
  pass


def main():
  description = __doc__.format(version=VERSION)

  parser = argparse.ArgumentParser(description=description,
                                   formatter_class=CustomArgParseFormatter)

  parser.add_argument('-i', '--input_config',
                      required=True,
                      help='The path to the input config file (required).')
  parser.add_argument('-p', '--pipeline_config',
                      required=True,
                      help='The path to the pipeline config file (required).')
  parser.add_argument('-c', '--cloud_url',
                      default=None,
                      help='The Google Cloud Storage URL to upload to.')
  parser.add_argument('-o', '--output',
                      default='output_files',
                      help='The output folder to write files to. ' +
                           'Used even if uploading to cloud storage.')

  args = parser.parse_args()

  # Check if the directory for outputted Packager files exists, and if it
  # does, delete it and remake a new one.
  if os.path.exists(args.output):
    shutil.rmtree(args.output)
  os.mkdir(args.output)

  controller = ControllerNode()

  with open(args.input_config) as f:
    input_config_dict = yaml.load(f)
  with open(args.pipeline_config) as f:
    pipeline_config_dict = yaml.load(f)

  if args.cloud_url:
    if not args.cloud_url.startswith('gs://'):
      parser.error('Invalid cloud URL, only gs:// URLs are supported currently')

  try:
    controller.start(args.output, input_config_dict, pipeline_config_dict,
                     args.cloud_url)
  except:
    # If the controller throws an exception during startup, we want to call
    # stop() to shut down any external processes that have already been started.
    # Then, re-raise the exception.
    controller.stop()
    raise

  # Sleep so long as the pipeline is still running.
  while controller.is_running():
    try:
      time.sleep(1)
    except KeyboardInterrupt:
      # Sometimes ffmpeg/packager take a while to be killed, so this signal
      # handler will kill both running processes as there is SIGINT signal.
      controller.stop()
      break

if __name__ == '__main__':
  main()
