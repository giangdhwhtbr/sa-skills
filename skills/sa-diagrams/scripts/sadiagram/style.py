"""The one shared style: fills per node kind, arrow per interaction kind, containers per group kind."""

from __future__ import annotations

FONT = "fontFamily=Helvetica;fontSize=12;"

# kind -> (fill, stroke, extra)
NODE_KINDS: dict[str, tuple[str, str, str]] = {
    "core": ("#dae8fc", "#6c8ebf", ""),
    "supporting": ("#d5e8d4", "#82b366", ""),
    "generic": ("#e1d5e7", "#9673a6", ""),
    "scheduled": ("#d5e8d4", "#000000", "strokeWidth=3;"),
    "bff-route": ("#ffe6cc", "#d79b00", ""),
    "gateway": ("#ffe6cc", "#d79b00", ""),
    "identity-provider": ("#f8cecc", "#b85450", "strokeWidth=2;"),
    "broker": ("#ffe6cc", "#d79b00", ""),
    "datastore": ("#ffe6cc", "#d79b00", ""),
    "client": ("#f5f5f5", "#666666", ""),
    "external": ("#f5f5f5", "#666666", "dashed=1;"),
    "actor": ("#ffffff", "#333333", ""),
    "aggregate-root": ("#dae8fc", "#6c8ebf", "strokeWidth=2;fontStyle=1;"),
    "entity": ("#ffffff", "#6c8ebf", ""),
    "value-object": ("#f5f5f5", "#999999", "dashed=1;"),
    "event": ("#ffe6cc", "#d79b00", "fontStyle=2;"),
    "note": ("#fff2cc", "#d6b656", ""),
    "step": ("#ffffff", "#333333", ""),
}

# kind -> (colour, dashed, end arrow)
EDGE_KINDS: dict[str, tuple[str, bool, str]] = {
    "sync": ("#1A73E8", False, "endArrow=block;endFill=1;"),
    "async": ("#E8A400", True, "endArrow=block;endFill=1;"),
    "auth": ("#7B1FA2", False, "endArrow=block;endFill=1;"),
    "data": ("#00897B", False, "endArrow=block;endFill=1;"),
    "external": ("#7F7F7F", True, "endArrow=block;endFill=1;"),
    "reference": ("#333333", True, "endArrow=open;endFill=0;"),
    "compensate": ("#D32F2F", True, "endArrow=block;endFill=1;"),
    "use": ("#333333", False, "endArrow=open;endFill=0;"),
    "include": ("#333333", True, "endArrow=open;endFill=0;"),
}

# kind -> (fill, stroke, extra)
GROUP_KINDS: dict[str, tuple[str, str, str]] = {
    "plain": ("none", "#999999", ""),
    "band-core": ("#f2f7fd", "#6c8ebf", ""),
    "band-supporting": ("#f3f9f2", "#82b366", ""),
    "band-generic": ("#f7f2f9", "#9673a6", ""),
    "layer": ("#fafafa", "#999999", ""),
    "aggregate": ("none", "#6c8ebf", "dashed=1;"),
    "region": ("none", "#00A4A6", "dashed=1;"),
    "vpc": ("none", "#8C4FFF", ""),
    "zone": ("none", "#147EBA", "dashed=1;"),
    "subnet-public": ("#E9F3E6", "#7AA116", ""),
    "subnet-app": ("#E6F2F8", "#147EBA", ""),
    "subnet-data": ("#FAF0E6", "#D86613", ""),
}

NODE_LABELS: dict[str, str] = {
    "core": "Core subdomain",
    "supporting": "Supporting subdomain",
    "generic": "Generic subdomain",
    "scheduled": "Scheduled service",
    "bff-route": "Gateway route",
    "gateway": "API gateway",
    "identity-provider": "Identity provider",
    "broker": "Message broker",
    "datastore": "Data store",
    "client": "Client",
    "external": "External system",
    "actor": "Actor",
    "aggregate-root": "Aggregate root",
    "entity": "Entity",
    "value-object": "Value object",
    "event": "Domain event",
    "step": "Function",
}

EDGE_LABELS: dict[str, str] = {
    "sync": "Sync call",
    "async": "Async event",
    "auth": "Authentication",
    "data": "Data access",
    "external": "External call",
    "reference": "ID reference",
    "compensate": "Compensation",
    "use": "Uses",
    "include": "Includes / extends",
}

_SHAPES: dict[str, str] = {
    "box": "rounded=1;arcSize=12;whiteSpace=wrap;html=1;",
    "ellipse": "ellipse;whiteSpace=wrap;html=1;",
    "hexagon": "shape=hexagon;perimeter=hexagonPerimeter2;fixedSize=1;size=14;whiteSpace=wrap;html=1;",
    "cylinder": "shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=10;whiteSpace=wrap;html=1;",
    "actor": "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;outlineConnect=0;html=1;",
    "lifeline": "shape=umlLifeline;perimeter=lifelinePerimeter;container=0;collapsible=0;size=40;"
                "whiteSpace=wrap;html=1;",
    "note": "shape=note;size=14;whiteSpace=wrap;html=1;align=left;verticalAlign=top;spacingLeft=6;",
    "text": "text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;",
}


def node_style(kind: str, shape: str = "box") -> str:
    """draw.io style for a node; the fill depends only on the kind, so a kind looks the same everywhere."""
    fill, stroke, extra = NODE_KINDS[kind]
    if shape == "text":
        return _SHAPES["text"] + FONT
    return f"{_SHAPES[shape]}fillColor={fill};strokeColor={stroke};{extra}{FONT}"


def icon_style(kind: str, icon: str) -> str:
    """AWS resource icon with the label below; the stroke keeps the kind's colour."""
    _, stroke, _ = NODE_KINDS[kind]
    return ("sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#ED7100;strokeColor=#ffffff;dashed=0;"
            "verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;aspect=fixed;"
            f"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{icon};labelBorderColor={stroke};{FONT}")


def edge_style(kind: str) -> str:
    colour, dashed, arrow = EDGE_KINDS[kind]
    return (f"html=1;rounded=0;{arrow}strokeColor={colour};strokeWidth=2;fontColor={colour};"
            f"labelBackgroundColor=#ffffff;{'dashed=1;' if dashed else ''}{FONT}")


def group_style(kind: str) -> str:
    fill, stroke, extra = GROUP_KINDS[kind]
    return (f"rounded=0;whiteSpace=wrap;html=1;container=1;collapsible=0;fillColor={fill};strokeColor={stroke};"
            f"verticalAlign=top;align=left;spacingLeft=8;fontStyle=1;{extra}{FONT}")


def title_style() -> str:
    return "text;html=1;align=left;verticalAlign=middle;fontStyle=1;fontSize=18;fontFamily=Helvetica;"


def end_label_style(kind: str) -> str:
    colour, _, _ = EDGE_KINDS[kind]
    return (f"edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];fontStyle=1;"
            f"fontColor={colour};labelBackgroundColor=#ffffff;{FONT}")
