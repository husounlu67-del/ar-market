"""
AR MARKET - PAZAR ALARM SISTEMI (Termux / Telefon)
=====================================================
Versiyon : 20260504210807
Calistir : python ar_alarm.py
Durdur   : Ctrl+C

Gereksinimler (bir kez):
  pkg install python tcpdump
"""

import struct, socket, subprocess, time, os, sys, urllib.request, urllib.parse
import json as _json, ssl as _ssl
from datetime import datetime

# =============================================
#  AYARLAR
# =============================================
VERSION          = "20260504210807"
GITHUB_RAW_URL   = "https://raw.githubusercontent.com/husounlu67-del/ar-market/main/ar_alarm.py"
SCRIPT_PATH      = os.path.abspath(__file__)
PCAP_PATH        = "/data/local/tmp/ar_alarm_scan.pcap"
GAME_SERVER      = "213.238.175.102"

# -- Telegram ---------------------------------
# -- Telegram (Alarm botu) --------------------
TELEGRAM_TOKEN   = "8094835962:AAEdADtpFdeR9MK6f_2SJ3u5flCfR4mCMjI"
TELEGRAM_CHAT_IDS = ["1598896323", "8610188409"]
# -- Telegram (Durum botu - sessiz) -----------
STATUS_TOKEN     = "8779317188:AAGIhv8v6YrRNScdPkyLJTNBaZtezIf3dPg"
STATUS_CHAT_ID   = "1598896323"
STATUS_INTERVAL  = 15 * 60  # 15 dakikada bir
# ---------------------------------------------
# ---------------------------------------------

ALARM_LIST = [
    {"name": "Hell Strike +1", "max_price": 2100000000, "item_ids": ["a51ae308"]},
    {"name": "Hell Strike +2", "max_price": 21000000001, "item_ids": ["a61ae308"]},
    {"name": "Hell Strike +3", "max_price": 210000000011, "item_ids": ["a71ae308"]},
    {"name": "Hell Strike +4", "max_price": 21000000001, "item_ids": ["a81ae308"]},
    {"name": "Hell Strike +5", "max_price": 21000000001, "item_ids": ["a91ae308"]},
    {"name": "Hell Strike +6", "max_price": 21000000001, "item_ids": ["aa1ae308"]},
]
# =============================================

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}", flush=True)

# ── VERSIYON KONTROL & OTOMATIK GUNCELLEME ───────────────────────
def check_update():
    try:
        ctx = _ssl._create_unverified_context()
        with urllib.request.urlopen(GITHUB_RAW_URL, timeout=10, context=ctx) as r:
            new_code = r.read().decode("utf-8")
        # VERSION satirini bul
        for line in new_code.splitlines():
            if line.startswith("VERSION"):
                new_ver = line.split("=")[1].strip().strip('"').strip("'")
                if new_ver != VERSION:
                    log(f"  Yeni versiyon bulundu: {new_ver} (mevcut: {VERSION})")
                    log("  Script guncelleniyor...")
                    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
                        f.write(new_code)
                    log("  Guncellendi! Yeniden baslatiliyor...")
                    os.execv(sys.executable, [sys.executable, SCRIPT_PATH])
                else:
                    log(f"  Versiyon guncel: {VERSION}")
                return
    except Exception as e:
        log(f"  Guncelleme kontrolu basarisiz: {e}")

# ── TCPDUMP (dogrudan telefon icinde) ────────────────────────────
def run_shell(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=20)
        return r
    except Exception as e:
        log(f"Shell hata: {e}")
        return None

def start_tcpdump():
    log("Tcpdump baslatiliyor...")
    # Termux tcpdump yolu
    tcpdump_bin = "/data/data/com.termux/files/usr/bin/tcpdump"
    run_shell("su -c 'killall tcpdump 2>/dev/null'")
    time.sleep(1)
    run_shell(f"su -c 'rm -f {PCAP_PATH}'")
    run_shell("su -c 'chmod 755 /data/local/tmp'")
    run_shell(f"chmod 755 {tcpdump_bin} 2>/dev/null")
    proc = subprocess.Popen(
        f"su -c '{tcpdump_bin} -i any -s 0 tcp -w {PCAP_PATH}'",
        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
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
    except:
        pass
    return 0

def pull_pcap():
    # Termux: pcap zaten telefonda, direkt oku
    try:
        # Okunabilir yap
        run_shell(f"su -c 'chmod 644 {PCAP_PATH}'")
        # Termux home'a kopyala
        local = os.path.join(os.path.expanduser("~"), "ar_alarm_scan.pcap")
        run_shell(f"su -c 'cp {PCAP_PATH} {local} && chmod 644 {local}'")
        if os.path.exists(local) and os.path.getsize(local) > 24:
            run_shell(f"su -c 'rm -f {PCAP_PATH}'")
            return local
    except Exception as e:
        log(f"  Pcap kopyalama hatasi: {e}")
    return None

def read_packets(path):
    packets = []
    link_type = 1
    try:
        with open(path, "rb") as f:
            magic = f.read(4)
            if len(magic) < 4: return packets, link_type
            endian = "<" if magic == b"\xd4\xc3\xb2\xa1" else ">"
            gh = f.read(20)
            if len(gh) == 20:
                link_type = struct.unpack(endian + "I", gh[16:20])[0]
            while True:
                hdr = f.read(16)
                if len(hdr) < 16: break
                _, _, incl_len, _ = struct.unpack(endian + "IIII", hdr)
                data = f.read(incl_len)
                if len(data) == incl_len:
                    packets.append(data)
    except Exception as e:
        log(f"Pcap okuma hatasi: {e}")
    return packets, link_type

def extract_server_payloads(packets, link_type=1):
    result = b""
    for pkt in packets:
        try:
            if len(pkt) < 20: continue
            if link_type == 276:
                # LINUX_SLL2: 20 byte header, EtherType at bytes 0-1
                if len(pkt) < 20: continue
                et = struct.unpack(">H", pkt[0:2])[0]
                if et != 0x0800: continue
                ip_start = 20
            elif link_type == 113:
                # LINUX_SLL: 16 byte header, EtherType at bytes 14-15
                if len(pkt) < 16: continue
                et = struct.unpack(">H", pkt[14:16])[0]
                if et != 0x0800: continue
                ip_start = 16
            else:
                # Ethernet: EtherType at bytes 12-13
                if len(pkt) < 14: continue
                et = struct.unpack(">H", pkt[12:14])[0]
                if et != 0x0800: continue
                ip_start = 14
            if len(pkt) <= ip_start + 20: continue
            if (pkt[ip_start] >> 4) != 4: continue
            ihl      = (pkt[ip_start] & 0x0F) * 4
            proto    = pkt[ip_start + 9]
            if proto != 6: continue
            tcp_start = ip_start + ihl
            if len(pkt) <= tcp_start + 20: continue
            data_off  = ((pkt[tcp_start + 12] >> 4) & 0xF) * 4
            payload   = pkt[tcp_start + data_off:]
            if len(payload) >= 10: result += payload
        except: pass
    return result

def parse_market_records(data):
    records, seen, n, i = [], set(), len(data), 0
    while i < n - 22:
        if data[i] == 0xaa and i + 1 < n and data[i+1] == 0x55:
            i += 2; continue
        if i + 2 > n: break
        name_len = struct.unpack("<H", data[i:i+2])[0]
        if not (2 <= name_len <= 25):
            i += 1; continue
        name_start = i + 2
        name_end   = name_start + name_len * 2
        if name_end + 20 > n:
            i += 1; continue
        try:
            name = data[name_start:name_end].decode("utf-16-le")
        except:
            i += 1; continue
        if not (all(32 <= ord(c) < 127 for c in name) and len(name) >= 2):
            i += 1; continue
        j = name_end
        item_count = 0
        while j + 20 <= n:
            item_id = data[j+1:j+5].hex()
            price   = struct.unpack("<I", data[j+9:j+13])[0]
            if 10_000 <= price <= 9_999_999_999 and all(x == 0 for x in data[j+13:j+20]):
                key = (name, item_id, price)
                if key not in seen:
                    seen.add(key)
                    records.append({"seller": name, "item_id": item_id, "price": price})
                item_count += 1
                j += 20
            else:
                break
        if item_count > 0:
            i = j
        else:
            i += 1
    return records

def parse_per_packet(pkts, link_type=1):
    """Her TCP paketini ayri ayri parse et - dogrulama icin."""
    verified = set()
    for pkt in pkts:
        try:
            if link_type == 276:
                if len(pkt) < 22 or struct.unpack(">H", pkt[0:2])[0] != 0x0800: continue
                ip_start = 20
            elif link_type == 113:
                if len(pkt) < 16: continue
                if struct.unpack(">H", pkt[14:16])[0] != 0x0800: continue
                ip_start = 16
            else:
                if len(pkt) < 14: continue
                if struct.unpack(">H", pkt[12:14])[0] != 0x0800: continue
                ip_start = 14
            if len(pkt) <= ip_start + 20: continue
            if (pkt[ip_start] >> 4) != 4: continue
            ihl = (pkt[ip_start] & 0x0F) * 4
            if pkt[ip_start + 9] != 6: continue
            ts = ip_start + ihl
            if len(pkt) <= ts + 20: continue
            doff = ((pkt[ts + 12] >> 4) & 0xF) * 4
            data = pkt[ts + doff:]
            if len(data) < 22: continue
            n = len(data)
            i = 0
            while i < n - 22:
                if data[i] == 0xaa and i+1 < n and data[i+1] == 0x55:
                    i += 2; continue
                if i + 2 > n: break
                name_len = struct.unpack("<H", data[i:i+2])[0]
                if not (2 <= name_len <= 25): i += 1; continue
                name_start = i + 2
                name_end   = name_start + name_len * 2
                if name_end + 20 > n: i += 1; continue
                try:
                    name = data[name_start:name_end].decode("utf-16-le")
                except:
                    i += 1; continue
                if not (all(32 <= ord(c) < 127 for c in name) and len(name) >= 2):
                    i += 1; continue
                j = name_end
                item_count = 0
                while j + 20 <= n:
                    item_id = data[j+1:j+5].hex()
                    price   = struct.unpack("<I", data[j+9:j+13])[0]
                    if 10_000 <= price <= 9_999_999_999 and all(x == 0 for x in data[j+13:j+20]):
                        verified.add((name, item_id, price))
                        item_count += 1
                        j += 20
                    else:
                        break
                if item_count > 0: i = j
                else: i += 1
        except:
            pass
    return verified

def check_alarms(records, pkts=None, link_type=1):
    if not records:
        log("  Kayit bulunamadi.")
        return
    log(f"  {len(records)} kayit / {len(set(r['item_id'] for r in records))} unique ID analiz ediliyor...")

    # Dogrulama: ayni kayitlari paket paket de parse et
    verified = None
    if pkts:
        verified = parse_per_packet(pkts, link_type)
        log(f"  Dogrulama: bireysel paketlerde {len(verified)} kayit bulundu")

    cheapest = {}
    for r in records:
        iid = r["item_id"]
        if iid not in cheapest or r["price"] < cheapest[iid]["price"]:
            cheapest[iid] = r
    all_alarm_ids = set(iid for alarm in ALARM_LIST for iid in alarm["item_ids"])
    fired = 0
    for alarm in ALARM_LIST:
        hits = [cheapest[iid] for iid in alarm["item_ids"] if iid in cheapest]
        if not hits: continue
        best = min(hits, key=lambda x: x["price"])
        if best["price"] <= alarm["max_price"]:
            # Dogrulama: bu kayit bireysel pakette de goruldumu?
            if verified is not None:
                key = (best["seller"], best["item_id"], best["price"])
                if key not in verified:
                    log(f"  ! SAHTE ALARM ENGELLENDI: {alarm['name']} @ {best['price']:,} gold")
                    log(f"    Birlesik akisda var, bireysel pakette yok (paket siniri hatasi)")
                    continue
            fire_alarm(alarm["name"], best["seller"], best["price"], alarm["max_price"])
            fired += 1
        else:
            pct = best["price"] / alarm["max_price"] * 100
            log(f"  x {alarm['name']:<35} {best['price']:>14,}  (esik {alarm['max_price']:,}  %{pct:.0f})")
    unknown = {iid: cheapest[iid] for iid in cheapest if iid not in all_alarm_ids}
    if unknown:
        log(f"  [{len(unknown)} bilinmeyen ID pazarda goruldu]")
    if fired == 0: log("  -> Esik altinda alarm yok.")
    else:          log(f"  *** {fired} ALARM ATESLENEDI! ***")

def send_telegram(text):
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            url     = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = _json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
            req     = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            ctx     = _ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                body = resp.read().decode("utf-8")
                if '"ok":true' in body:
                    log(f"  Telegram gonderildi -> {chat_id}")
                else:
                    log(f"  Telegram hatasi ({chat_id}): {body[:200]}")
        except Exception as e:
            log(f"  Telegram hatasi ({chat_id}): {e}")

def send_status(text):
    try:
        url     = f"https://api.telegram.org/bot{STATUS_TOKEN}/sendMessage"
        payload = _json.dumps({
            "chat_id": STATUS_CHAT_ID,
            "text": text,
            "disable_notification": True
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        ctx = _ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            body = resp.read().decode("utf-8")
            if '"ok":true' in body:
                log("  Durum mesaji gonderildi.")
            else:
                log(f"  Durum botu hatasi: {body[:200]}")
    except Exception as e:
        log(f"  Durum botu hatasi: {e}")

def fire_alarm(item_name, seller, price, max_price):
    log(f"  *** ALARM *** {item_name}  |  {seller}  |  {price:,} gold")
    msg = (
        "AR MARKET ALARMI!\n\n"
        f"Item  : {item_name}\n"
        f"Satan : {seller}\n"
        f"Fiyat : {price:,} gold\n"
        f"Esik  : {max_price:,} gold\n\n"
        "Hemen pazari ac!"
    )
    send_telegram(msg)

def main():
    log("=" * 60)
    log("  AR MARKET - PAZAR ALARM SISTEMI (Termux)")
    log(f"  Versiyon: {VERSION}")
    log("=" * 60)
    log(f"  Alarm sayisi  : {len(ALARM_LIST)}")
    log(f"  Toplam item_id: {sum(len(a['item_ids']) for a in ALARM_LIST)}")
    log("")

    # Versiyon kontrolu
    log("Guncelleme kontrol ediliyor...")
    check_update()
    log("")

    # Telegram testi
    log("Telegram test ediliyor...")
    send_telegram(f"AR Market Alarm baslatildi (v{VERSION}). {len(ALARM_LIST)} alarm aktif.")
    send_status(f"✅ AR Market Alarm baslatildi (v{VERSION})\n⏱ {datetime.now().strftime('%H:%M')} — {len(ALARM_LIST)} alarm aktif")
    log("")

    scan_no           = 0
    tcpdump_proc      = None
    last_update_check = time.time()
    last_status_send  = time.time()
    UPDATE_CHECK_INTERVAL = 60

    BURST_THRESHOLD = 15_000
    BURST_END_SECS  = 3

    try:
        while True:
            if tcpdump_proc is None or tcpdump_proc.poll() is not None:
                tcpdump_proc = start_tcpdump()
                log("Dinleniyor... Pazar persomenini ac.")

            prev_size     = get_pcap_size()
            in_burst      = False
            burst_end_cnt = 0

            while True:
                time.sleep(1)

                # Versiyon kontrolu (her 60sn)
                if time.time() - last_update_check >= UPDATE_CHECK_INTERVAL:
                    last_update_check = time.time()
                    log("Guncelleme kontrol ediliyor...")
                    check_update()

                # Durum mesaji (her 15 dakika, sessiz)
                if time.time() - last_status_send >= STATUS_INTERVAL:
                    last_status_send = time.time()
                    send_status(f"✅ AR Market Alarm calisiyor (v{VERSION})\n⏱ {datetime.now().strftime('%H:%M')} — {scan_no} tarama yapildi")

                sz   = get_pcap_size()
                diff = sz - prev_size
                prev_size = sz

                if diff >= BURST_THRESHOLD:
                    if not in_burst:
                        log(f"  >>> Pazar verisi geliyor! ({diff//1024}KB/sn)")
                        in_burst = True
                    burst_end_cnt = 0
                elif in_burst:
                    burst_end_cnt += 1
                    if burst_end_cnt >= BURST_END_SECS:
                        log(f"  Burst bitti, analiz basliyor...")
                        break
                else:
                    pass

            scan_no += 1
            log(f"\nTarama #{scan_no}")
            local_pcap = pull_pcap()
            if not local_pcap:
                log("  Pcap alinamadi.")
                in_burst = False
                burst_end_cnt = 0
                continue

            pkts, link_type = read_packets(local_pcap)
            payload = extract_server_payloads(pkts, link_type)
            log(f"  {len(pkts)} paket / {len(payload):,} byte server verisi")

            # Gecici dosyayi temizle
            try: os.remove(local_pcap)
            except: pass

            if len(payload) == 0:
                log("  Server verisi bos.")
            else:
                recs = parse_market_records(payload)
                check_alarms(recs, pkts, link_type)

            log("  30sn sonra persomeni tekrar ac.")
            log("")
            run_shell("su -c 'killall tcpdump 2>/dev/null'")
            time.sleep(2)
            tcpdump_proc  = None
            in_burst      = False
            burst_end_cnt = 0

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
