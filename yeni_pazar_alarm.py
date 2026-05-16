"""
NOWA - UST PAZAR ALARM SISTEMI (Termux / Telefon)
==================================================
Calistir : python yeni_pazar_alarm.py
Durdur   : Ctrl+C

Gereksinimler (bir kez):
  pkg install python tcpdump
"""

import struct, subprocess, time, os, sys, urllib.request
import json as _json, ssl as _ssl
from datetime import datetime

# =============================================
#  AYARLAR
# =============================================
VERSION           = "20260516150000"
GITHUB_RAW_URL    = "https://raw.githubusercontent.com/husounlu67-del/ar-market/main/yeni_pazar_alarm.py"
SCRIPT_PATH       = os.path.abspath(__file__)
PCAP_PATH         = "/data/local/tmp/yeni_pazar_scan.pcap"
GAME_PORT         = 19001
MSG_TYPE          = 0x000002f8

TELEGRAM_TOKEN    = "8094835962:AAEdADtpFdeR9MK6f_2SJ3u5flCfR4mCMjI"
TELEGRAM_CHAT_IDS = ["1598896323", "8610188409"]

GIST_ID   = "b6cae757f7651b69b99cb25b23bbf683"
GIST_FILE = "ar_alarm.json"

PCAP_ESIK = 15_000   # 15 KB — bu kadar dolunca analiz et

ALARM_LIST = []
ID_MAP     = {}
# =============================================


def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}", flush=True)


# ── GIST'TEN ALARM LISTESI ────────────────────────────────────────
def load_gist_config():
    global ALARM_LIST, ID_MAP
    log("Gist'ten alarm listesi yukleniyor...")
    try:
        ctx = _ssl._create_unverified_context()
        req = urllib.request.Request(
            f"https://api.github.com/gists/{GIST_ID}",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "yeni-pazar-alarm"
            }
        )
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            gist_raw = _json.loads(r.read().decode("utf-8"))

        content = gist_raw.get("files", {}).get(GIST_FILE, {}).get("content", "")
        if not content:
            log("  HATA: Gist dosyasi bos!")
            return False

        gist_data = _json.loads(content)
        prices    = gist_data.get("prices", {})
        saved_ids = gist_data.get("savedIDs", {})

        alarm_lines = []
        id_map_tmp  = {}

        for key, id_data in saved_ids.items():
            parts = key.split("|")
            if len(parts) < 3:
                continue
            cat_id, item_name, level_name = parts[0], parts[1], parts[2]
            confirmed_ids = id_data.get("confirmed", [])
            if not confirmed_ids:
                continue
            for id_ in confirmed_ids:
                id_map_tmp[id_] = f"{item_name} {level_name}"
            try:
                lv_data   = prices.get(cat_id, {}).get(item_name, {}).get(level_name, {})
                price_val = lv_data.get("price", "")
                active    = lv_data.get("active", False)
            except Exception:
                price_val, active = "", False
            if active and price_val:
                try:
                    max_price = int(str(price_val).replace(",", "").replace(".", ""))
                except ValueError:
                    continue
                alarm_lines.append({
                    "name"     : f"{item_name} {level_name}",
                    "max_price": max_price,
                    "item_ids" : confirmed_ids
                })

        ALARM_LIST.clear()
        ALARM_LIST.extend(alarm_lines)
        ID_MAP.update(id_map_tmp)
        log(f"  {len(ALARM_LIST)} alarm yuklendi, {len(ID_MAP)} ID haritasinda")
        return True
    except Exception as e:
        log(f"  Gist yukleme hatasi: {e}")
        return False


# ── VERSIYON KONTROL ─────────────────────────────────────────────
def check_update():
    try:
        ctx = _ssl._create_unverified_context()
        with urllib.request.urlopen(GITHUB_RAW_URL, timeout=10, context=ctx) as r:
            new_code = r.read().decode("utf-8")
        for line in new_code.splitlines():
            if line.startswith("VERSION"):
                new_ver = line.split("=")[1].strip().strip('"').strip("'")
                if new_ver != VERSION:
                    log(f"  Yeni versiyon: {new_ver}. Guncelleniyor...")
                    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
                        f.write(new_code)
                    os.execv(sys.executable, [sys.executable, SCRIPT_PATH])
                else:
                    log(f"  Versiyon guncel: {VERSION}")
                return
    except Exception as e:
        log(f"  Guncelleme kontrolu basarisiz: {e}")


# ── TCPDUMP ──────────────────────────────────────────────────────
def run_shell(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, timeout=20)
    except Exception as e:
        log(f"Shell hata: {e}")
        return None


def get_pcap_size():
    """Pcap dosyasinin boyutunu dogrudan os.path ile al — wc -c'den daha guvenilir."""
    try:
        if os.path.exists(PCAP_PATH):
            return os.path.getsize(PCAP_PATH)
    except Exception:
        pass
    return 0


def start_tcpdump():
    tcpdump_bin = "/data/data/com.termux/files/usr/bin/tcpdump"
    # Onceki tcpdump'i oldur, eski pcap'i sil
    run_shell("su -c 'killall tcpdump 2>/dev/null'")
    time.sleep(1)
    run_shell(f"su -c 'rm -f {PCAP_PATH}'")
    run_shell("su -c 'chmod 755 /data/local/tmp'")
    # Yeni tcpdump baslat
    proc = subprocess.Popen(
        f"su -c '{tcpdump_bin} -i any -s 0 tcp port {GAME_PORT} -w {PCAP_PATH}'",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2)
    log(f"  Tcpdump basladi (PID: {proc.pid}). Ust pazari ac.")
    return proc


def stop_tcpdump(proc):
    try:
        proc.kill()
    except Exception:
        pass
    run_shell("su -c 'killall tcpdump 2>/dev/null'")
    time.sleep(1)


def read_pcap_raw():
    """
    Pcap'i oku, tum paket verilerini ham olarak birlestir.
    Link/IP/TCP parse etme — AA55+0x2F8 pattern yeterince ozgun.
    """
    result = b""
    try:
        # Once Termux home'a kopyala (root izni olmadan okuyabilmek icin)
        local = os.path.join(os.path.expanduser("~"), "yp_scan.pcap")
        run_shell(f"su -c 'chmod 644 {PCAP_PATH} && cp {PCAP_PATH} {local} && chmod 644 {local}'")
        if not os.path.exists(local) or os.path.getsize(local) < 24:
            return result

        with open(local, "rb") as f:
            # Global header: 24 byte
            magic = f.read(4)
            if len(magic) < 4:
                return result
            endian = "<" if magic == b"\xd4\xc3\xb2\xa1" else ">"
            f.read(20)  # global header rest
            # Paketleri oku
            while True:
                hdr = f.read(16)
                if len(hdr) < 16:
                    break
                _, _, incl_len, _ = struct.unpack(endian + "IIII", hdr)
                if incl_len > 65535:
                    break
                pkt = f.read(incl_len)
                if len(pkt) == incl_len:
                    result += pkt  # ham paket verisini direkt ekle

        # Gecici dosyayi sil
        try:
            os.remove(local)
        except Exception:
            pass
        # Orijinal pcap'i de sil
        run_shell(f"su -c 'rm -f {PCAP_PATH}'")

    except Exception as e:
        log(f"  Pcap okuma hatasi: {e}")
    return result


# ── YENİ PAZAR PROTOKOL (29-byte bloklar) ────────────────────────
def parse_yeni_pazar(stream):
    """
    Frame: AA55 [2B frame_len LE] [4B msgtype=0x2F8] [9B header] [itemler]
    Her item: 29 byte
      blk[0:4]   = listing_id (atla)
      blk[4:8]   = item_id (LE hex)
      blk[8:17]  = qty + unknown
      blk[17:22] = price (5 byte Little Endian)
      blk[22:29] = padding
    frame_len > 1000 → pazar verisi
    frame_len <= 1000 → heartbeat/kontrol, atla
    """
    records, seen = [], set()
    n = len(stream)
    i = 0
    while i < n - 8:
        if stream[i] != 0xaa or stream[i+1] != 0x55:
            i += 1
            continue
        if i + 8 > n:
            break
        frame_len = struct.unpack_from("<H", stream, i+2)[0]
        msg_type  = struct.unpack_from("<I", stream, i+4)[0]
        if msg_type != MSG_TYPE or frame_len <= 1000:
            i += 2
            continue
        # Pazar frame bulundu
        items_start = i + 15
        j = items_start
        while j + 29 <= n:
            if stream[j] == 0xaa and stream[j+1] == 0x55:
                break
            item_id = stream[j+4:j+8].hex()
            price   = int.from_bytes(stream[j+17:j+22], 'little')
            if item_id != "00000000" and 100_000 <= price <= 999_999_999_999_999:
                key = (item_id, price)
                if key not in seen:
                    seen.add(key)
                    records.append({"item_id": item_id, "price": price})
            j += 29
        i = j if j > items_start else i + 2
    return records


# ── ALARM KONTROL ─────────────────────────────────────────────────
def check_alarms(records):
    if not records:
        log("  Parse edilen item yok.")
        return
    unique = len(set(r["item_id"] for r in records))
    log(f"  {len(records)} kayit / {unique} unique ID")
    cheapest = {}
    for r in records:
        iid = r["item_id"]
        if iid not in cheapest or r["price"] < cheapest[iid]["price"]:
            cheapest[iid] = r
    fired = 0
    for alarm in ALARM_LIST:
        hits = [cheapest[iid] for iid in alarm["item_ids"] if iid in cheapest]
        if not hits:
            continue
        best = min(hits, key=lambda x: x["price"])
        if best["price"] <= alarm["max_price"]:
            fire_alarm(alarm["name"], best["item_id"], best["price"], alarm["max_price"])
            fired += 1
        else:
            pct = best["price"] / alarm["max_price"] * 100
            log(f"  x {alarm['name']:<40} {best['price']:>20,}  (%{pct:.0f})")
    if fired == 0:
        log("  -> Esik altinda alarm yok.")
    else:
        log(f"  *** {fired} ALARM ATESLENEDI! ***")


def send_telegram(text):
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            url     = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = _json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
            req     = urllib.request.Request(url, data=payload,
                          headers={"Content-Type": "application/json"})
            ctx = _ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                body = resp.read().decode("utf-8")
                if '"ok":true' in body:
                    log(f"  Telegram gonderildi -> {chat_id}")
                else:
                    log(f"  Telegram hatasi: {body[:100]}")
        except Exception as e:
            log(f"  Telegram hatasi: {e}")


def fire_alarm(item_name, item_id, price, max_price):
    id_label = ID_MAP.get(item_id, item_id)
    log(f"  *** ALARM *** {item_name} | {price:,} gold")
    msg = (
        "NOWA UST PAZAR ALARMI!\n\n"
        f"Item  : {item_name}\n"
        f"ID    : {id_label}\n"
        f"Fiyat : {price:,} gold\n"
        f"Esik  : {max_price:,} gold\n\n"
        "Hemen ust pazari ac!"
    )
    send_telegram(msg)


# ── MAIN ─────────────────────────────────────────────────────────
def main():
    log("=" * 65)
    log("  NOWA - UST PAZAR ALARM SISTEMI (Termux)")
    log(f"  Versiyon: {VERSION}")
    log("=" * 65)
    log("")

    log("Guncelleme kontrol ediliyor...")
    check_update()
    log("")

    if not load_gist_config() or not ALARM_LIST:
        log("HATA: Alarm listesi bos! HTML'den aktifle -> 'Ust Pazar Alarm Indir'.")
        return

    send_telegram(
        f"NOWA Ust Pazar Alarm baslatildi (v{VERSION}).\n"
        f"{len(ALARM_LIST)} alarm aktif."
    )
    log("")

    scan_no = 0

    try:
        while True:
            # 1. Tcpdump baslat (eski pcap icinde siliniyor)
            tcpdump_proc = start_tcpdump()

            # 2. Pcap 15KB dolana kadar bekle — 2sn'de bir kontrol et
            log(f"  Bekleniyor... (esik: {PCAP_ESIK:,} byte)")
            while True:
                time.sleep(2)
                sz = get_pcap_size()
                if sz >= PCAP_ESIK:
                    log(f"  {sz:,} byte geldi. Analiz basliyor...")
                    break

            # 3. Tcpdump durdur
            stop_tcpdump(tcpdump_proc)

            # 4. Pcap'i oku ve isle
            scan_no += 1
            log(f"Tarama #{scan_no}")
            stream = read_pcap_raw()
            log(f"  Ham veri: {len(stream):,} byte")

            if len(stream) < 100:
                log("  Veri cok az, atlaniyor.")
            else:
                recs = parse_yeni_pazar(stream)
                log(f"  Parse edilen item: {len(recs)}")
                check_alarms(recs)

            log("  Bitti. Ust pazari tekrar ac.")
            log("")

    except KeyboardInterrupt:
        log("\nKullanici durdurdu.")
    except Exception as e:
        log(f"\nBeklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()
    finally:
        log("Tcpdump durduruluyor...")
        run_shell("su -c 'killall tcpdump 2>/dev/null'")
        log("Sistem durduruldu.")


if __name__ == "__main__":
    main()
