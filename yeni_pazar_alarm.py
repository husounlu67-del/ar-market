"""
NOWA - UST PAZAR ALARM SISTEMI (Termux / Telefon)
==================================================
Calistir : python yeni_pazar_alarm.py
Durdur   : Ctrl+C

Gereksinimler (bir kez):
  pkg install python tcpdump

Alarm listesi GitHub Gist'ten otomatik yuklenir.
Eski pazar scriptiyle (ar_alarm.py) FARKLI Termux sekmesinde calistir.
"""

import struct, subprocess, time, os, sys, urllib.request
import json as _json, ssl as _ssl
from datetime import datetime

# =============================================
#  AYARLAR
# =============================================
VERSION           = "20260516120000"
GITHUB_RAW_URL    = "https://raw.githubusercontent.com/husounlu67-del/ar-market/main/yeni_pazar_alarm.py"
SCRIPT_PATH       = os.path.abspath(__file__)
PCAP_PATH         = "/data/local/tmp/yeni_pazar_scan.pcap"
GAME_PORT         = 19001
MSG_TYPE          = 0x000002f8

# -- Telegram ---------------------------------
TELEGRAM_TOKEN    = "8094835962:AAEdADtpFdeR9MK6f_2SJ3u5flCfR4mCMjI"
TELEGRAM_CHAT_IDS = ["1598896323", "8610188409"]
# ---------------------------------------------

# -- GitHub Gist (alarm listesi buradan gelir)
GIST_ID   = "b6cae757f7651b69b99cb25b23bbf683"
GIST_FILE = "ar_alarm.json"
# ---------------------------------------------

# Pcap esigi: bu kadar byte gelince analiz et
PCAP_ESIK = 15_000   # 15 KB

# =============================================
ALARM_LIST = []
ID_MAP     = {}
# =============================================


def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}", flush=True)


# ── GIST'TEN ALARM LISTESI YUKLE ─────────────────────────────────
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

            # ID haritasini doldur
            for id_ in confirmed_ids:
                id_map_tmp[id_] = f"{item_name} {level_name}"

            # Aktif alarm var mi?
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


# ── VERSIYON KONTROL & OTOMATIK GUNCELLEME ───────────────────────
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
                    log("  Guncellendi! Yeniden baslatiliyor...")
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


def start_tcpdump():
    log("Tcpdump baslatiliyor (port 19001)...")
    tcpdump_bin = "/data/data/com.termux/files/usr/bin/tcpdump"
    run_shell("su -c 'killall tcpdump 2>/dev/null'")
    time.sleep(1)
    run_shell(f"su -c 'rm -f {PCAP_PATH}'")
    run_shell("su -c 'chmod 755 /data/local/tmp'")
    proc = subprocess.Popen(
        f"su -c '{tcpdump_bin} -i any -s 0 tcp port {GAME_PORT} -w {PCAP_PATH}'",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2)
    log(f"  Tcpdump aktif (PID: {proc.pid})")
    return proc


def get_pcap_size():
    try:
        r = run_shell(f"su -c 'wc -c {PCAP_PATH} 2>/dev/null'")
        if r and r.stdout:
            parts = r.stdout.decode("utf-8", errors="ignore").strip().split()
            if parts:
                return int(parts[0])
    except Exception:
        pass
    return 0


def pull_pcap():
    """Pcap'i Termux home klasorune kopyala ve yolu don."""
    try:
        run_shell(f"su -c 'chmod 644 {PCAP_PATH}'")
        local = os.path.join(os.path.expanduser("~"), "yeni_pazar_scan.pcap")
        run_shell(f"su -c 'cp {PCAP_PATH} {local} && chmod 644 {local}'")
        if os.path.exists(local) and os.path.getsize(local) > 24:
            run_shell(f"su -c 'rm -f {PCAP_PATH}'")
            return local
    except Exception as e:
        log(f"  Pcap kopyalama hatasi: {e}")
    return None


# ── PCAP PARSE ───────────────────────────────────────────────────
def read_packets(path):
    packets, link_type = [], 1
    try:
        with open(path, "rb") as f:
            magic = f.read(4)
            if len(magic) < 4:
                return packets, link_type
            endian    = "<" if magic == b"\xd4\xc3\xb2\xa1" else ">"
            gh        = f.read(20)
            if len(gh) == 20:
                link_type = struct.unpack(endian + "I", gh[16:20])[0]
            while True:
                hdr = f.read(16)
                if len(hdr) < 16:
                    break
                _, _, incl_len, _ = struct.unpack(endian + "IIII", hdr)
                data = f.read(incl_len)
                if len(data) == incl_len:
                    packets.append(data)
    except Exception as e:
        log(f"Pcap okuma hatasi: {e}")
    return packets, link_type


def extract_payloads(packets, link_type=1):
    """Tum TCP payload'larini birlestir — IP filtresi YOK, port filtresi tcpdump'ta."""
    result = b""
    for pkt in packets:
        try:
            if link_type == 276:
                if len(pkt) < 22 or struct.unpack(">H", pkt[0:2])[0] != 0x0800:
                    continue
                ip_start = 20
            elif link_type == 113:
                if len(pkt) < 16:
                    continue
                if struct.unpack(">H", pkt[14:16])[0] != 0x0800:
                    continue
                ip_start = 16
            else:
                if len(pkt) < 14:
                    continue
                if struct.unpack(">H", pkt[12:14])[0] != 0x0800:
                    continue
                ip_start = 14
            if len(pkt) <= ip_start + 20:
                continue
            if (pkt[ip_start] >> 4) != 4:
                continue
            ihl       = (pkt[ip_start] & 0x0F) * 4
            if pkt[ip_start + 9] != 6:
                continue
            tcp_start = ip_start + ihl
            if len(pkt) <= tcp_start + 20:
                continue
            data_off  = ((pkt[tcp_start + 12] >> 4) & 0xF) * 4
            payload   = pkt[tcp_start + data_off:]
            if len(payload) >= 10:
                result += payload
        except Exception:
            pass
    return result


# ── YENİ PAZAR PROTOKOL (29-byte bloklar) ────────────────────────
def parse_yeni_pazar(stream):
    """
    Frame basligi: AA55 [2B frame_len LE] [4B msgtype=0x2F8] [9B header]
    Her item bloku: 29 byte
      blk[0:4]   = listing_id  (atla)
      blk[4:8]   = item_id     (LE hex)
      blk[8:17]  = qty+unk
      blk[17:22] = price       (5 byte Little Endian)
      blk[22:29] = padding
    Filtre: frame_len > 1000 → pazar verisi | <= 1000 → heartbeat/kontrol
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
        # Pazar frame bulundu — itemleri oku
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
        log("  Kayit bulunamadi.")
        return

    unique = len(set(r["item_id"] for r in records))
    log(f"  {len(records)} kayit / {unique} unique ID analiz ediliyor...")

    # Her item_id icin en ucuz fiyati bul
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
            req     = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"}
            )
            ctx = _ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                body = resp.read().decode("utf-8")
                if '"ok":true' in body:
                    log(f"  Telegram gonderildi -> {chat_id}")
                else:
                    log(f"  Telegram hatasi ({chat_id}): {body[:200]}")
        except Exception as e:
            log(f"  Telegram hatasi ({chat_id}): {e}")


def fire_alarm(item_name, item_id, price, max_price):
    id_label = ID_MAP.get(item_id, item_id)
    log(f"  *** ALARM *** {item_name}  |  {id_label}  |  {price:,} gold")
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
        log("HATA: Alarm listesi yuklenemedi veya bos!")
        log("  Cozum: HTML'de bir itemi aktifle -> 'Ust Pazar Alarm Indir' tusuna bas.")
        return

    send_telegram(
        f"NOWA Ust Pazar Alarm baslatildi (v{VERSION}).\n"
        f"{len(ALARM_LIST)} alarm aktif."
    )
    log("")

    scan_no      = 0
    tcpdump_proc = None

    try:
        while True:
            # Tcpdump baslat
            if tcpdump_proc is None or tcpdump_proc.poll() is not None:
                tcpdump_proc = start_tcpdump()
                log("Dinleniyor... Ust pazari ac.")

            # Pcap boyutunu izle — PCAP_ESIK kadar veri gelince analiz et
            while True:
                time.sleep(2)
                sz = get_pcap_size()
                if sz >= PCAP_ESIK:
                    log(f"  Yeterli veri ({sz:,} byte). Analiz yapiliyor...")
                    break

            # Tcpdump durdur
            try:
                tcpdump_proc.kill()
            except Exception:
                pass
            run_shell("su -c 'killall tcpdump 2>/dev/null'")
            time.sleep(1)
            tcpdump_proc = None

            # Pcap'i al ve isle
            scan_no += 1
            log(f"\nTarama #{scan_no}")
            local_pcap = pull_pcap()
            if not local_pcap:
                log("  Pcap alinamadi, devam ediliyor...")
                continue

            pkts, link_type = read_packets(local_pcap)
            stream = extract_payloads(pkts, link_type)
            log(f"  {len(pkts)} paket / {len(stream):,} byte TCP verisi")

            try:
                os.remove(local_pcap)
            except Exception:
                pass

            if len(stream) == 0:
                log("  TCP verisi bos.")
            else:
                recs = parse_yeni_pazar(stream)
                log(f"  Parse edilen item: {len(recs)}")
                check_alarms(recs)

            log("  30sn sonra ust pazari tekrar ac.")
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
