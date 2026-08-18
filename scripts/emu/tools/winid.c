// Print CoreGraphics window ids matching a name substring, one "id<TAB>owner<TAB>title" per line.
//
// WHY: jusemu.py's screenshot path asked System Events for melonDS's window id
// and got error -1728 -- melonDS's Qt window is not exposed through the
// accessibility API, so no permission grant fixes it. Capturing the whole
// display instead does not work either: melonDS usually sits behind the
// terminal, and a display capture only sees what is on top.
//
// `screencapture -l <windowid>` CAN capture an occluded window, so all we need
// is the id. CoreGraphics hands it over with no extra permission and no Python
// dependency, which is why this is 40 lines of C rather than a pyobjc install.
//
// Build: cc -O2 -framework CoreGraphics -framework CoreFoundation -o winid winid.c
// Usage: ./winid melonDS
#include <CoreFoundation/CoreFoundation.h>
#include <CoreGraphics/CoreGraphics.h>
#include <stdio.h>
#include <string.h>

static void cfstr(CFStringRef s, char *out, size_t n) {
    out[0] = 0;
    if (s) CFStringGetCString(s, out, (CFIndex)n, kCFStringEncodingUTF8);
}

// "--front" prints the owner of the frontmost on-screen window. Needed because
// screencapture -l on an OCCLUDED window can return a STALE cached backing store:
// captures come back byte-identical while the emulator is plainly still running,
// which reads as "the screen never changed" and is the worst kind of silent
// failure. Captures are only trustworthy while melonDS is frontmost.
static int print_front(void) {
    CFArrayRef list = CGWindowListCopyWindowInfo(
        kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements,
        kCGNullWindowID);
    if (!list) return 2;
    int rc = 1;
    // The on-screen list is ordered front to back.
    for (CFIndex i = 0; i < CFArrayGetCount(list); i++) {
        CFDictionaryRef d = CFArrayGetValueAtIndex(list, i);
        char owner[256];
        cfstr(CFDictionaryGetValue(d, kCGWindowOwnerName), owner, sizeof owner);
        CFNumberRef ln = CFDictionaryGetValue(d, kCGWindowLayer);
        int layer = 0;
        if (ln) CFNumberGetValue(ln, kCFNumberIntType, &layer);
        if (layer != 0) continue;   // skip menu bar, docks, overlays
        printf("%s\n", owner);
        rc = 0;
        break;
    }
    CFRelease(list);
    return rc;
}

int main(int argc, char **argv) {
    if (argc > 1 && strcmp(argv[1], "--front") == 0) return print_front();
    const char *needle = argc > 1 ? argv[1] : "melonDS";
    // Exclude desktop elements; include off-screen so an occluded or minimised
    // window still shows up -- that is the whole point.
    CFArrayRef list = CGWindowListCopyWindowInfo(
        kCGWindowListOptionAll | kCGWindowListExcludeDesktopElements, kCGNullWindowID);
    if (!list) { fprintf(stderr, "CGWindowListCopyWindowInfo failed\n"); return 2; }
    int found = 0;
    for (CFIndex i = 0; i < CFArrayGetCount(list); i++) {
        CFDictionaryRef d = CFArrayGetValueAtIndex(list, i);
        char owner[256], title[512];
        cfstr(CFDictionaryGetValue(d, kCGWindowOwnerName), owner, sizeof owner);
        cfstr(CFDictionaryGetValue(d, kCGWindowName), title, sizeof title);
        if (!strcasestr(owner, needle) && !strcasestr(title, needle)) continue;
        CFNumberRef num = CFDictionaryGetValue(d, kCGWindowNumber);
        int id = 0;
        if (num) CFNumberGetValue(num, kCFNumberIntType, &id);
        // Skip the 1x1 and 0-size helper windows Qt creates; they capture blank.
        CFDictionaryRef b = CFDictionaryGetValue(d, kCGWindowBounds);
        double w = 0, h = 0;
        if (b) {
            CGRect r;
            if (CGRectMakeWithDictionaryRepresentation(b, &r)) { w = r.size.width; h = r.size.height; }
        }
        printf("%d\t%.0fx%.0f\t%s\t%s\n", id, w, h, owner, title);
        found++;
    }
    CFRelease(list);
    if (!found) { fprintf(stderr, "no window matching %s\n", needle); return 1; }
    return 0;
}
