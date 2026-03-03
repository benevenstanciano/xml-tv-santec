from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

from .parser import Programme


@dataclass(frozen=True)
class Channel:
    id: str
    display_name: str
    lang: str
    icon: str | None = None


def _xmltv_time(dt: datetime) -> str:
    dt_utc = dt.astimezone(timezone.utc)
    return dt_utc.strftime("%Y%m%d%H%M%S +0000")


def build_xmltv_single_channel(
    channel: Channel,
    programmes: Iterable[Programme],
) -> str:
    tv = Element("tv")
    tv.set("generator-info-name", "xmltv-epg-generator")

    ch = SubElement(tv, "channel", {"id": channel.id})
    SubElement(ch, "display-name").text = channel.display_name
    if channel.icon:
        SubElement(ch, "icon", {"src": channel.icon})

    for p in programmes:
        pr = SubElement(
            tv,
            "programme",
            {
                "start": _xmltv_time(p.start),
                "stop": _xmltv_time(p.stop),
                "channel": channel.id,
            },
        )
        title_el = SubElement(pr, "title", {"lang": channel.lang})
        title_el.text = p.title

        if p.desc:
            desc_el = SubElement(pr, "desc", {"lang": channel.lang})
            desc_el.text = p.desc

    rough = tostring(tv, encoding="utf-8")
    pretty = minidom.parseString(rough).toprettyxml(indent="  ", encoding="utf-8")
    return pretty.decode("utf-8")
