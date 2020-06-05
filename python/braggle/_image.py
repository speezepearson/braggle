from typing import Optional
from . import Element
from . import protobuf_helpers
from .protobuf import element_pb2

class Image(Element):
  def __init__(self, url: str, format: Optional[str] = None):
    """
    :param str url: the URL to load the image from
    :param str format: the image's file format, or None to guess from url
    """
    super().__init__()

    self._url = url
    if format is None:
      format = url.rsplit(".", 1)[-1]
      if (format == "") or not format.isalnum():
        raise ValueError('no format given and none guessable from url '+url)
    self.format = format

  @property
  def url(self) -> str:
    return self._url
  @url.setter
  def url(self, url: str) -> None:
    self._url = url
    self.mark_dirty()

  def to_protobuf(self) -> element_pb2.Element:
    return protobuf_helpers.tag('img', attributes={'src': self.url})
