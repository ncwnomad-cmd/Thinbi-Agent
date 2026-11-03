import json
import os
import time
import urllib.request
import urllib.error
from pathlib import Path

BASE = os.environ.get("THINBI_AGENT_URL", "http://127.0.0.1:3000")
COMFY = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")
ROOT = Path(os.environ.get("COLORING_BOOK_ROOT", r"D:\Coloring Books\Cozy Christmas Coloring Book"))
PAGES = ROOT / "Pages"
STATE = ROOT / "generation_progress.json"
TARGET_ILLUSTRATIONS = 50
BATCH_SIZE = 5

# Each entry describes a distinct full-page scene; combinations produce 98 different compositions.
themes = [
("living room", ["a tall Christmas tree beside a simple fireplace", "a cozy armchair with a knitted blanket and a small side table", "a wide mantel with three stockings and a large wreath", "a window seat with a mug and a snowy view", "a stack of wrapped gifts beside a little tree", "a rocking chair beside a basket of logs", "a large Christmas tree with oversized baubles", "a fireplace with a simple garland and two candles", "a toy train circling a small tree", "a pair of slippers beside a decorated present"]),
("kitchen", ["a tray of star-shaped cookies on a counter", "a large mixing bowl with a wooden spoon and cookie cutters", "a gingerbread house with a simple candy roof", "a kettle beside two holiday mugs", "a plate of cinnamon rolls and a jar", "a hanging bunch of candy canes and a wreath", "a pie cooling beside oven mitts", "a cookie tin with a ribbon and a few cookies", "a festive table with a simple centerpiece", "a tall jar filled with large round ornaments"]),
("front porch", ["a front door with a large wreath and two lanterns", "a pair of boots beside a potted evergreen", "a bench with a cushion and wrapped parcel", "a simple sled leaning beside the door", "a large welcome mat and two planters", "a garland around a porch window", "a pair of skates beside a lantern", "a basket of pinecones and a big bow", "a rocking chair with a warm blanket", "a mailbox with a holiday bow"]),
("snowy village", ["a small cottage with smoke curling from its chimney", "a village shop with a striped awning", "a tiny chapel with a simple bell tower", "a row of three snow-covered cottages", "a bakery window with a large wreath", "a village bridge over a little stream", "a street lamp beside a snow-covered bench", "a horse-drawn sleigh outside a cottage", "a small train station with a wreath", "a cozy bookshop with a decorated door"]),
("Christmas market", ["a wooden stall selling wreaths", "a cocoa stand with two large mugs", "a toy stall with a teddy bear and drum", "a basket of oversized baubles", "a simple market cart with evergreen branches", "a stall displaying gingerbread houses", "a lantern-lit gift stall", "a stack of wrapped parcels on a counter", "a stall with knitted hats and mittens", "a small carousel horse beside a tree"]),
("bedroom", ["a bed with a patchwork quilt and a small tree", "a bedside table with a book and a star lamp", "a window with curtains and a snowy view", "a cozy blanket folded on a chair", "a pair of stockings hanging by the bed", "a dresser with a wreath and two candles", "a teddy bear holding a wrapped gift", "a simple garland above the headboard", "a pair of slippers beside a rug", "a small tree decorated with large bows"]),
("dining room", ["a long table with a simple holiday centerpiece", "a place setting with a plate and folded napkin", "a large serving dish with covered lid", "a sideboard with candles and a wreath", "a bowl of apples and oranges with evergreen", "a chair with a ribbon tied around it", "a simple tiered cake stand with treats", "a pitcher and two glasses beside a centerpiece", "a large bowl of wrapped crackers", "a table runner with three big stars"]),
("forest cabin", ["a log cabin door with a wreath", "a stack of firewood beside a snowy window", "a lantern hanging from a wooden post", "a small evergreen decorated with bows", "a pair of snowshoes leaning by the door", "a sled beside a tree stump", "a cozy window with a candle", "a bench with a folded blanket", "a birdhouse on a snow-covered tree", "a stack of gifts on a wooden porch"]),
("craft room", ["a large wreath with a wide ribbon", "a pair of scissors beside broad ribbon rolls", "three handmade paper stars hanging from a branch", "a basket of yarn with two knitting needles", "a simple handmade ornament on a worktable", "a row of three greeting cards", "a spool of ribbon beside a gift box", "a large stocking ready to be decorated", "a craft table with a glue pot and big shapes", "a basket of pinecones and large bows"]),
("toy room", ["a teddy bear beside a rocking horse", "a wooden toy train with three simple cars", "a large toy drum with two drumsticks", "a dollhouse with a wreath on its door", "a toy robot beside a wrapped present", "a stack of three building blocks shaped as gifts", "a rocking horse with a wide ribbon", "a toy boat beside a little tree", "a large jack-in-the-box with a star", "a toy truck carrying a Christmas tree"]),
("garden", ["a snow-covered birdbath with two birds", "a garden gate with a large wreath", "a pair of garden boots beside a planter", "a bird feeder hanging from a branch", "a simple snowman beside a fence", "a wheelbarrow carrying evergreen branches", "a bench beneath a decorated tree", "a lantern beside a snow-covered path", "a small greenhouse with a wreath", "a watering can beside a potted fir"]),
("bakery", ["a large gingerbread person on a tray", "a stack of iced cookies with simple shapes", "a cake with three large candles", "a pie with a simple star-shaped crust", "a row of cupcakes with big frosting swirls", "a bread basket tied with a bow", "a large pretzel and a mug", "a cookie jar beside a rolling pin", "a gingerbread cottage on a cake stand", "a tray of holiday buns"]),
("winter pond", ["a pair of ice skates beside a bench", "a small wooden hut beside the frozen pond", "two mittens resting on a snow-covered rail", "a sled beside a snowbank", "a lantern and a thermos on a bench", "a pair of ducks near the snowy edge", "a snowman wearing a scarf", "a small evergreen beside the pond", "a wooden sign with a star decoration", "a pair of boots beside a hockey stick"]),
("attic", ["a large open trunk filled with ornaments", "a stack of vintage gift boxes", "a rocking chair beside a round window", "a teddy bear beside an old toy train", "a large star ornament hanging from a beam", "a basket of stockings and ribbons", "a small tree beside a dormer window", "a pair of wooden skis beside a trunk", "a stack of holiday books with a bow", "a lantern beside a wrapped parcel"])
]

scenes = []
for room, objects in themes:
    for obj in objects:
        scenes.append(f"A simple charming Christmas coloring page set in a cozy {room}: {obj}. Show only a few large recognizable objects, thick closed outlines, broad open coloring areas, centered composition, generous white margins.")

def get_json(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))

def post_json(url, data):
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))

def file_for(page):
    matches = [p for p in PAGES.glob(f"Page_{page:03d}*.png") if "TEST" not in p.stem.upper()]
    return sorted(matches, key=lambda p: p.name.lower())[:1]

def save_state(next_page, completed, status, error=None):
    state = {
        "target_illustrations": TARGET_ILLUSTRATIONS,
        "target_interior_pages": TARGET_ILLUSTRATIONS * 2,
        "completed_pages": sorted(set(completed)),
        "next_page": next_page,
        "status": status,
        "error": error,
        "updated_unix": int(time.time())
    }
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")

def wait_for_empty_queue(timeout_seconds=10800):
    start = time.time()
    while time.time() - start < timeout_seconds:
        q = get_json(COMFY + "/queue")
        if len(q.get("queue_running", [])) == 0 and len(q.get("queue_pending", [])) == 0:
            return
        time.sleep(20)
    raise TimeoutError("ComfyUI queue did not clear within three hours.")

def main():
    PAGES.mkdir(parents=True, exist_ok=True)
    wait_for_empty_queue()

    # Existing numbered art is preserved; TEST files are deliberately ignored.
    completed = {n for n in range(1, TARGET_ILLUSTRATIONS + 1) if file_for(n)}
    while len(completed) < TARGET_ILLUSTRATIONS:
        missing = [n for n in range(1, TARGET_ILLUSTRATIONS + 1) if n not in completed]
        start_page = missing[0]
        batch_pages = [start_page]
        for number in missing[1:]:
            if number == batch_pages[-1] + 1 and len(batch_pages) < BATCH_SIZE:
                batch_pages.append(number)
            else:
                break

        batch_scenes = [scenes[number - 1] for number in batch_pages]
        result = post_json(BASE + "/coloring-book/batch", {
            "scenes": batch_scenes,
            "startPage": start_page
        })
        if not result.get("ok") or len(result.get("jobs", [])) != len(batch_pages):
            raise RuntimeError("Agent rejected batch: " + json.dumps(result))

        save_state(start_page, completed, f"queued_pages_{start_page}_to_{batch_pages[-1]}")
        wait_for_empty_queue()

        missing_batch = [number for number in batch_pages if not file_for(number)]
        if missing_batch:
            raise RuntimeError(f"Missing generated files for pages: {missing_batch}")

        completed.update(batch_pages)
        next_page = next(
            (number for number in range(1, TARGET_ILLUSTRATIONS + 1) if number not in completed),
            TARGET_ILLUSTRATIONS + 1
        )
        save_state(next_page, completed, "generating" if next_page <= TARGET_ILLUSTRATIONS else "all_illustrations_generated")

    save_state(TARGET_ILLUSTRATIONS + 1, completed, "all_illustrations_generated")
    print(json.dumps({
        "status": "all_illustrations_generated",
        "target_illustrations": TARGET_ILLUSTRATIONS,
        "target_interior_pages": TARGET_ILLUSTRATIONS * 2,
        "count": len(completed),
        "pages": sorted(completed)
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        try:
            previous = json.loads(STATE.read_text(encoding="utf-8"))
            completed = previous.get("completed_pages", [])
            next_page = previous.get("next_page", 0)
        except Exception:
            completed, next_page = [], 0
        save_state(next_page, completed, "stopped_with_error", str(exc))
        raise
