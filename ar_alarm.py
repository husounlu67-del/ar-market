"""
AR MARKET - PAZAR ALARM SISTEMI (Termux / Telefon)
=====================================================
Versiyon : 20260515221856
Calistir : python ar_alarm.py
Durdur   : Ctrl+C

Gereksinimler (bir kez):
  pkg install python tcpdump

OZELLIKLER:
  - Normal pazar (eski sistem) alarmı
  - Ust pazar (port 19001) alarmı
  - Her ikisi tek scriptte, Termux'ta calısır
"""

import struct, socket, subprocess, time, os, sys, threading, urllib.request, urllib.parse
import json as _json, ssl as _ssl
from datetime import datetime

# =============================================
#  AYARLAR
# =============================================
VERSION          = "20260515221856"
GITHUB_RAW_URL   = "https://raw.githubusercontent.com/husounlu67-del/ar-market/main/ar_alarm.py"
SCRIPT_PATH      = os.path.abspath(__file__)

# Normal pazar pcap
PCAP_PATH        = "/data/local/tmp/ar_alarm_scan.pcap"
# Ust pazar pcap
PCAP_PATH_UST    = "/data/local/tmp/ar_alarm_ust.pcap"

GAME_SERVER      = "213.238.175.102"
UST_PAZAR_PORT   = 19001

# Ust pazar frame sabitleri
UST_MSG_TYPE     = 0x000002f8
UST_BLOCK_SIZE   = 29
UST_HEADER_SIZE  = 15   # aa55 dahil
UST_MIN_FRAME    = 1000
UST_MIN_PRICE    = 100_000
UST_MAX_PRICE    = 999_999_999_999_999
UST_BURST_BYTES  = 15_000   # 15KB gelince analiz et

# -- Telegram ---------------------------------
# -- Telegram (Alarm botu) --------------------
TELEGRAM_TOKEN   = "8094835962:AAEdADtpFdeR9MK6f_2SJ3u5flCfR4mCMjI"
TELEGRAM_CHAT_IDS = ["1598896323", "8610188409"]
# ---------------------------------------------
# ---------------------------------------------

ALARM_LIST = [
    {"name": "Hope's Frozen Staff +0", "max_price": 5000000, "item_ids": ["b078450b"]},
    {"name": "Hope's Frozen Staff +1", "max_price": 5000000, "item_ids": ["317a450b"]},
    {"name": "Hope's Frozen Staff +2", "max_price": 5000000, "item_ids": ["327a450b"]},
    {"name": "Hope's Frozen Staff +3", "max_price": 5000000, "item_ids": ["337a450b"]},
    {"name": "Hope's Frozen Staff +4", "max_price": 5000000, "item_ids": ["347a450b"]},
    {"name": "Hope's Frozen Staff +5", "max_price": 6000000, "item_ids": ["357a450b"]},
    {"name": "Hope's Frozen Staff +6", "max_price": 6000000, "item_ids": ["367a450b"]},
    {"name": "Hope's Frozen Staff +7", "max_price": 40000000, "item_ids": ["377a450b"]},
    {"name": "Hope's Frozen Staff +8", "max_price": 220000000, "item_ids": ["387a450b"]},
    {"name": "Hope's Frozen Staff +9", "max_price": 5000000000, "item_ids": ["397a450b"]},
    {"name": "Hope's Frozen Staff +10", "max_price": 5000000000, "item_ids": ["3a7a450b"]},
    {"name": "Iceberg Staff +1", "max_price": 5000000, "item_ids": ["6dfb460b"]},
    {"name": "Iceberg Staff +2", "max_price": 5000000, "item_ids": ["6efb460b"]},
    {"name": "Iceberg Staff +3", "max_price": 5000000, "item_ids": ["6ffb460b"]},
    {"name": "Iceberg Staff +4", "max_price": 10000000, "item_ids": ["70fb460b"]},
    {"name": "Iceberg Staff +5", "max_price": 20000000, "item_ids": ["71fb460b"]},
    {"name": "Iceberg Staff +6", "max_price": 40000000, "item_ids": ["72fb460b"]},
    {"name": "Iceberg Staff +7", "max_price": 55000000, "item_ids": ["73fb460b"]},
    {"name": "Iceberg Staff +8", "max_price": 300000000, "item_ids": ["74fb460b"]},
    {"name": "Iceberg Staff +9", "max_price": 10000000000, "item_ids": ["75fb460b"]},
    {"name": "Iceberg Staff +10", "max_price": 10000000000, "item_ids": ["76fb460b"]},
    {"name": "Iceberg Staff Reb+1", "max_price": 55000000, "item_ids": ["a522470b"]},
    {"name": "Iceberg Staff Reb+2", "max_price": 60000000, "item_ids": ["a622470b"]},
    {"name": "Iceberg Staff Reb+3", "max_price": 100000000, "item_ids": ["a722470b"]},
    {"name": "Iceberg Staff Reb+4", "max_price": 150000000, "item_ids": ["a822470b"]},
    {"name": "Iceberg Staff Reb+5", "max_price": 222222222, "item_ids": ["a922470b"]},
    {"name": "Iceberg Staff Reb+6", "max_price": 222222222, "item_ids": ["aa22470b"]},
    {"name": "Iceberg Staff Reb+7", "max_price": 222222222, "item_ids": ["ab22470b"]},
    {"name": "Iceberg Staff Reb+8", "max_price": 222222222, "item_ids": ["ac22470b"]},
    {"name": "Iceberg Staff Reb+9", "max_price": 222222222, "item_ids": ["ad22470b"]},
    {"name": "Iceberg Staff Reb+10", "max_price": 2500000000, "item_ids": ["ae22470b"]},
    {"name": "Iceberg Staff Reb+11", "max_price": 2500000000, "item_ids": ["af22470b"]},
    {"name": "Iceberg Staff Reb+12", "max_price": 2500000000, "item_ids": ["b022470b"]},
    {"name": "Iceberg Staff Reb+13", "max_price": 5000000000, "item_ids": ["b122470b"]},
    {"name": "Iceberg Staff Reb+14", "max_price": 5000000000, "item_ids": ["b222470b"]},
    {"name": "Iceberg Staff Reb+15", "max_price": 5000000000, "item_ids": ["b322470b"]},
    {"name": "Iceberg Staff Reb+16", "max_price": 5000000000, "item_ids": ["b422470b"]},
    {"name": "Iceberg Staff Reb+17", "max_price": 5000000000, "item_ids": ["b522470b"]},
    {"name": "Iceberg Staff Reb+18", "max_price": 5000000000, "item_ids": ["b622470b"]},
    {"name": "Iceberg Staff Reb+19", "max_price": 5000000000, "item_ids": ["b722470b"]},
    {"name": "Iceberg Staff Reb+20", "max_price": 5000000000, "item_ids": ["b822470b"]},
    {"name": "Iceberg Staff Reb+21", "max_price": 5000000000, "item_ids": ["b922470b"]},
    {"name": "Katana Sword +0", "max_price": 75000000, "item_ids": ["2eedb107"]},
    {"name": "Katana Sword +1", "max_price": 75000000, "item_ids": ["9bedb107"]},
    {"name": "Katana Sword +2", "max_price": 75000000, "item_ids": ["9cedb107"]},
    {"name": "Katana Sword +3", "max_price": 75000000, "item_ids": ["9dedb107"]},
    {"name": "Katana Sword +4", "max_price": 75000000, "item_ids": ["9eedb107"]},
    {"name": "Katana Sword +5", "max_price": 220000000, "item_ids": ["9fedb107"]},
    {"name": "Katana Sword +6", "max_price": 220000000, "item_ids": ["a0edb107"]},
    {"name": "Katana Sword +7", "max_price": 220000000, "item_ids": ["a1edb107"]},
    {"name": "Katana Sword +8", "max_price": 220000000, "item_ids": ["a2edb107"]},
    {"name": "Katana Sword +9", "max_price": 5000000000, "item_ids": ["a3edb107"]},
    {"name": "Katana Sword +10", "max_price": 5000000000, "item_ids": ["a4edb107"]},
    {"name": "Katana Sword Reb+1", "max_price": 220000000, "item_ids": ["3314b207"]},
    {"name": "Katana Sword Reb+2", "max_price": 220000000, "item_ids": ["3414b207"]},
    {"name": "Katana Sword Reb+3", "max_price": 220000000, "item_ids": ["3514b207"]},
    {"name": "Katana Sword Reb+4", "max_price": 220000000, "item_ids": ["3614b207"]},
    {"name": "Katana Sword Reb+5", "max_price": 220000000, "item_ids": ["3714b207"]},
    {"name": "Katana Sword Reb+6", "max_price": 500000000, "item_ids": ["3814b207"]},
    {"name": "Katana Sword Reb+7", "max_price": 500000000, "item_ids": ["3914b207"]},
    {"name": "Katana Sword Reb+8", "max_price": 600000000, "item_ids": ["3a14b207"]},
    {"name": "Katana Sword Reb+9", "max_price": 1000000000, "item_ids": ["3b14b207"]},
    {"name": "Katana Sword Reb+10", "max_price": 5000000000, "item_ids": ["3c14b207"]},
    {"name": "Katana Sword Reb+11", "max_price": 5000000000, "item_ids": ["3d14b207"]},
    {"name": "Katana Sword Reb+12", "max_price": 5000000000, "item_ids": ["3e14b207"]},
    {"name": "Katana Sword Reb+13", "max_price": 5000000000, "item_ids": ["3f14b207"]},
    {"name": "Katana Sword Reb+14", "max_price": 5000000000, "item_ids": ["4014b207"]},
    {"name": "Katana Sword Reb+15", "max_price": 5000000000, "item_ids": ["4114b207"]},
    {"name": "Katana Sword Reb+16", "max_price": 5000000000, "item_ids": ["4214b207"]},
    {"name": "Katana Sword Reb+17", "max_price": 5000000000, "item_ids": ["4314b207"]},
    {"name": "Katana Sword Reb+18", "max_price": 5000000000, "item_ids": ["4414b207"]},
    {"name": "Katana Sword Reb+19", "max_price": 5000000000, "item_ids": ["4514b207"]},
    {"name": "Katana Sword Reb+20", "max_price": 5000000000, "item_ids": ["4614b207"]},
    {"name": "Katana Sword Reb+21", "max_price": 5000000000, "item_ids": ["4714b207"]},
    {"name": "Fireguard Hammer +0", "max_price": 220000000, "item_ids": ["b10ade0b"]},
    {"name": "Fireguard Hammer +1", "max_price": 220000000, "item_ids": ["390bde0b"]},
    {"name": "Fireguard Hammer +2", "max_price": 220000000, "item_ids": ["3a0bde0b"]},
    {"name": "Fireguard Hammer +3", "max_price": 220000000, "item_ids": ["3b0bde0b"]},
    {"name": "Fireguard Hammer +4", "max_price": 220000000, "item_ids": ["3c0bde0b"]},
    {"name": "Fireguard Hammer +5", "max_price": 220000000, "item_ids": ["3d0bde0b"]},
    {"name": "Fireguard Hammer +6", "max_price": 220000000, "item_ids": ["3e0bde0b"]},
    {"name": "Fireguard Hammer +7", "max_price": 220000000, "item_ids": ["3f0bde0b"]},
    {"name": "Fireguard Hammer +8", "max_price": 220000000, "item_ids": ["400bde0b"]},
    {"name": "Fireguard Hammer +9", "max_price": 5000000000, "item_ids": ["410bde0b"]},
    {"name": "Fireguard Hammer +10", "max_price": 5000000000, "item_ids": ["420bde0b"]},
    {"name": "Fireguard Hammer Reb+1", "max_price": 220000000, "item_ids": ["4932de0b"]},
    {"name": "Fireguard Hammer Reb+2", "max_price": 220000000, "item_ids": ["4a32de0b"]},
    {"name": "Fireguard Hammer Reb+3", "max_price": 220000000, "item_ids": ["4b32de0b"]},
    {"name": "Fireguard Hammer Reb+4", "max_price": 220000000, "item_ids": ["4c32de0b"]},
    {"name": "Fireguard Hammer Reb+5", "max_price": 220000000, "item_ids": ["4d32de0b"]},
    {"name": "Fireguard Hammer Reb+6", "max_price": 2000000000, "item_ids": ["4e32de0b"]},
    {"name": "Fireguard Hammer Reb+7", "max_price": 5000000000, "item_ids": ["4f32de0b"]},
    {"name": "Fireguard Hammer Reb+8", "max_price": 5000000000, "item_ids": ["5032de0b"]},
    {"name": "Fireguard Hammer Reb+9", "max_price": 5000000000, "item_ids": ["5132de0b"]},
    {"name": "Fireguard Hammer Reb+10", "max_price": 5000000000, "item_ids": ["5232de0b"]},
    {"name": "Fireguard Hammer Reb+11", "max_price": 5000000000, "item_ids": ["5332de0b"]},
    {"name": "Fireguard Hammer Reb+12", "max_price": 5000000000, "item_ids": ["5432de0b"]},
    {"name": "Fireguard Hammer Reb+13", "max_price": 5000000000, "item_ids": ["5532de0b"]},
    {"name": "Fireguard Hammer Reb+14", "max_price": 5000000000, "item_ids": ["5632de0b"]},
    {"name": "Fireguard Hammer Reb+15", "max_price": 5000000000, "item_ids": ["5732de0b"]},
    {"name": "Fireguard Hammer Reb+16", "max_price": 5000000000, "item_ids": ["5832de0b"]},
    {"name": "Fireguard Hammer Reb+17", "max_price": 5000000000, "item_ids": ["5932de0b"]},
    {"name": "Fireguard Hammer Reb+18", "max_price": 5000000000, "item_ids": ["5a32de0b"]},
    {"name": "Fireguard Hammer Reb+19", "max_price": 5000000000, "item_ids": ["5b32de0b"]},
    {"name": "Fireguard Hammer Reb+20", "max_price": 5000000000, "item_ids": ["5c32de0b"]},
    {"name": "Fireguard Hammer Reb+21", "max_price": 5000000000, "item_ids": ["5d32de0b"]},
    {"name": "Cold Dagger +0", "max_price": 100000000, "item_ids": ["565b1907"]},
    {"name": "Cold Dagger +1", "max_price": 100000000, "item_ids": ["cb5b1907", "575b1907"]},
    {"name": "Cold Dagger +2", "max_price": 100000000, "item_ids": ["cc5b1907", "585b1907"]},
    {"name": "Cold Dagger +3", "max_price": 100000000, "item_ids": ["cd5b1907", "595b1907"]},
    {"name": "Cold Dagger +4", "max_price": 120000000, "item_ids": ["ce5b1907", "5a5b1907"]},
    {"name": "Cold Dagger +5", "max_price": 220000000, "item_ids": ["cf5b1907", "5b5b1907"]},
    {"name": "Cold Dagger +6", "max_price": 220000000, "item_ids": ["d05b1907", "5c5b1907"]},
    {"name": "Cold Dagger +7", "max_price": 220000000, "item_ids": ["d15b1907", "5d5b1907"]},
    {"name": "Cold Dagger +8", "max_price": 220000000, "item_ids": ["d25b1907", "5e5b1907"]},
    {"name": "Cold Dagger +9", "max_price": 5000000000, "item_ids": ["d35b1907", "5f5b1907"]},
    {"name": "Cold Dagger +10", "max_price": 5000000000, "item_ids": ["d45b1907", "605b1907"]},
    {"name": "Light Storm Staff +1", "max_price": 5000000, "item_ids": ["1782480b"]},
    {"name": "Light Storm Staff +2", "max_price": 6000000, "item_ids": ["1882480b"]},
    {"name": "Light Storm Staff +3", "max_price": 8000000, "item_ids": ["1982480b"]},
    {"name": "Light Storm Staff +4", "max_price": 8000000, "item_ids": ["1a82480b"]},
    {"name": "Light Storm Staff +5", "max_price": 10000000, "item_ids": ["1b82480b"]},
    {"name": "Light Storm Staff +6", "max_price": 15000000, "item_ids": ["1c82480b"]},
    {"name": "Light Storm Staff +7", "max_price": 100000000, "item_ids": ["1d82480b"]},
    {"name": "Light Storm Staff +8", "max_price": 220000000, "item_ids": ["1e82480b"]},
    {"name": "Light Storm Staff Reb+1", "max_price": 100000000, "item_ids": ["63a9480b"]},
    {"name": "Light Storm Staff Reb+2", "max_price": 100000000, "item_ids": ["64a9480b"]},
    {"name": "Light Storm Staff Reb+3", "max_price": 150000000, "item_ids": ["65a9480b"]},
    {"name": "Light Storm Staff Reb+4", "max_price": 220000000, "item_ids": ["66a9480b"]},
    {"name": "Light Storm Staff Reb+5", "max_price": 220000000, "item_ids": ["67a9480b"]},
    {"name": "Light Storm Staff Reb+6", "max_price": 500000000, "item_ids": ["68a9480b"]},
    {"name": "Light Storm Staff Reb+7", "max_price": 500000000, "item_ids": ["69a9480b"]},
    {"name": "Light Storm Staff Reb+8", "max_price": 500000000, "item_ids": ["6aa9480b"]},
    {"name": "Light Storm Staff Reb+9", "max_price": 500000000, "item_ids": ["6ba9480b"]},
    {"name": "Light Storm Staff Reb+10", "max_price": 500000000, "item_ids": ["6ca9480b"]},
    {"name": "Light Storm Staff Reb+11", "max_price": 5000000000, "item_ids": ["6da9480b"]},
    {"name": "Light Storm Staff Reb+12", "max_price": 5000000000, "item_ids": ["6ea9480b"]},
    {"name": "Light Storm Staff Reb+13", "max_price": 5000000000, "item_ids": ["6fa9480b"]},
    {"name": "Light Storm Staff Reb+14", "max_price": 5000000000, "item_ids": ["70a9480b"]},
    {"name": "Light Storm Staff Reb+15", "max_price": 5000000000, "item_ids": ["71a9480b"]},
    {"name": "Light Storm Staff Reb+16", "max_price": 5000000000, "item_ids": ["72a9480b"]},
    {"name": "Light Storm Staff Reb+17", "max_price": 5000000000, "item_ids": ["73a9480b"]},
    {"name": "Light Storm Staff Reb+18", "max_price": 5000000000, "item_ids": ["74a9480b"]},
    {"name": "Light Storm Staff Reb+19", "max_price": 5000000000, "item_ids": ["75a9480b"]},
    {"name": "Light Storm Staff Reb+20", "max_price": 5000000000, "item_ids": ["76a9480b"]},
    {"name": "Light Storm Staff Reb+21", "max_price": 5000000000, "item_ids": ["77a9480b"]},
    {"name": "Arcane Bow +0", "max_price": 50000000, "item_ids": ["3047140a"]},
    {"name": "Arcane Bow +1", "max_price": 50000000, "item_ids": ["af47140a"]},
    {"name": "Arcane Bow +2", "max_price": 50000000, "item_ids": ["b047140a"]},
    {"name": "Arcane Bow +3", "max_price": 50000000, "item_ids": ["b147140a"]},
    {"name": "Arcane Bow +4", "max_price": 50000000, "item_ids": ["b247140a"]},
    {"name": "Arcane Bow +5", "max_price": 80000000, "item_ids": ["b347140a"]},
    {"name": "Arcane Bow +6", "max_price": 50000000, "item_ids": ["b447140a"]},
    {"name": "Arcane Bow +7", "max_price": 220000000, "item_ids": ["b547140a"]},
    {"name": "Arcane Bow +8", "max_price": 220000000, "item_ids": ["b647140a"]},
    {"name": "Arcane Bow Reb+1", "max_price": 220000000, "item_ids": ["6f6e140a"]},
    {"name": "Arcane Bow Reb+2", "max_price": 220000000, "item_ids": ["706e140a"]},
    {"name": "Arcane Bow Reb+3", "max_price": 220000000, "item_ids": ["716e140a"]},
    {"name": "Arcane Bow Reb+4", "max_price": 220000000, "item_ids": ["726e140a"]},
    {"name": "Arcane Bow Reb+5", "max_price": 220000000, "item_ids": ["736e140a"]},
    {"name": "Arcane Bow Reb+6", "max_price": 5000000000, "item_ids": ["746e140a"]},
    {"name": "Arcane Bow Reb+7", "max_price": 5000000000, "item_ids": ["756e140a"]},
    {"name": "Arcane Bow Reb+8", "max_price": 5000000000, "item_ids": ["766e140a"]},
    {"name": "Arcane Bow Reb+9", "max_price": 5000000000, "item_ids": ["776e140a"]},
    {"name": "Arcane Bow Reb+10", "max_price": 5000000000, "item_ids": ["786e140a"]},
    {"name": "Arcane Bow Reb+11", "max_price": 5000000000, "item_ids": ["796e140a"]},
    {"name": "Arcane Bow Reb+12", "max_price": 5000000000, "item_ids": ["7a6e140a"]},
    {"name": "Arcane Bow Reb+13", "max_price": 5000000000, "item_ids": ["7b6e140a"]},
    {"name": "Arcane Bow Reb+14", "max_price": 5000000000, "item_ids": ["7c6e140a"]},
    {"name": "Arcane Bow Reb+15", "max_price": 5000000000, "item_ids": ["7d6e140a"]},
    {"name": "Arcane Bow Reb+16", "max_price": 5000000000, "item_ids": ["7e6e140a"]},
    {"name": "Arcane Bow Reb+17", "max_price": 5000000000, "item_ids": ["7f6e140a"]},
    {"name": "Arcane Bow Reb+18", "max_price": 5000000000, "item_ids": ["806e140a"]},
    {"name": "Arcane Bow Reb+19", "max_price": 5000000000, "item_ids": ["816e140a"]},
    {"name": "Arcane Bow Reb+20", "max_price": 5000000000, "item_ids": ["826e140a"]},
    {"name": "Arcane Bow Reb+21", "max_price": 5000000000, "item_ids": ["836e140a"]},
    {"name": "Hell Strike +0", "max_price": 220000000, "item_ids": ["2f1ae308"]},
    {"name": "Hell Strike +1", "max_price": 220000000, "item_ids": ["a51ae308"]},
    {"name": "Hell Strike +2", "max_price": 220000000, "item_ids": ["a61ae308"]},
    {"name": "Hell Strike +3", "max_price": 220000000, "item_ids": ["a71ae308"]},
    {"name": "Hell Strike +4", "max_price": 220000000, "item_ids": ["a81ae308"]},
    {"name": "Hell Strike +5", "max_price": 220000000, "item_ids": ["a91ae308"]},
    {"name": "Hell Strike +6", "max_price": 220000000, "item_ids": ["aa1ae308"]},
    {"name": "Hell Strike +7", "max_price": 220000000, "item_ids": ["ab1ae308"]},
    {"name": "Hell Strike +8", "max_price": 220000000, "item_ids": ["ac1ae308"]},
    {"name": "Hell Strike Reb+1", "max_price": 220000000, "item_ids": ["1541e308"]},
    {"name": "Hell Strike Reb+2", "max_price": 220000000, "item_ids": ["1641e308"]},
    {"name": "Hell Strike Reb+3", "max_price": 220000000, "item_ids": ["1741e308"]},
    {"name": "Hell Strike Reb+4", "max_price": 220000000, "item_ids": ["1841e308"]},
    {"name": "Hell Strike Reb+5", "max_price": 220000000, "item_ids": ["1941e308"]},
    {"name": "Hell Strike Reb+6", "max_price": 5000000000, "item_ids": ["1a41e308"]},
    {"name": "Hell Strike Reb+7", "max_price": 5000000000, "item_ids": ["1b41e308"]},
    {"name": "Hell Strike Reb+8", "max_price": 5000000000, "item_ids": ["1c41e308"]},
    {"name": "Hell Strike Reb+9", "max_price": 5000000000, "item_ids": ["1d41e308"]},
    {"name": "Hell Strike Reb+10", "max_price": 5000000000, "item_ids": ["1e41e308"]},
    {"name": "Hell Strike Reb+11", "max_price": 5000000000, "item_ids": ["1f41e308"]},
    {"name": "Hell Strike Reb+12", "max_price": 5000000000, "item_ids": ["2041e308"]},
    {"name": "Hell Strike Reb+13", "max_price": 5000000000, "item_ids": ["2141e308"]},
    {"name": "Hell Strike Reb+14", "max_price": 5000000000, "item_ids": ["2241e308"]},
    {"name": "Hell Strike Reb+15", "max_price": 5000000000, "item_ids": ["2341e308"]},
    {"name": "Hell Strike Reb+16", "max_price": 5000000000, "item_ids": ["2441e308"]},
    {"name": "Hell Strike Reb+17", "max_price": 5000000000, "item_ids": ["2541e308"]},
    {"name": "Hell Strike Reb+18", "max_price": 5000000000, "item_ids": ["2641e308"]},
    {"name": "Hell Strike Reb+19", "max_price": 5000000000, "item_ids": ["2741e308"]},
    {"name": "Hell Strike Reb+20", "max_price": 5000000000, "item_ids": ["2841e308"]},
    {"name": "Hell Strike Reb+21", "max_price": 5000000000, "item_ids": ["2941e308"]},
    {"name": "HellFire Staff +1", "max_price": 25000000, "item_ids": ["f574450b"]},
    {"name": "HellFire Staff +2", "max_price": 50000000, "item_ids": ["f674450b"]},
    {"name": "HellFire Staff +3", "max_price": 50000000, "item_ids": ["f774450b"]},
    {"name": "HellFire Staff +4", "max_price": 50000000, "item_ids": ["f874450b"]},
    {"name": "HellFire Staff +5", "max_price": 50000000, "item_ids": ["f974450b"]},
    {"name": "HellFire Staff +6", "max_price": 50000000, "item_ids": ["fa74450b"]},
    {"name": "HellFire Staff +7", "max_price": 220000000, "item_ids": ["fb74450b"]},
    {"name": "HellFire Staff +8", "max_price": 220000000, "item_ids": ["fc74450b"]},
    {"name": "HellFire Staff Reb+1", "max_price": 220000000, "item_ids": ["e79b450b"]},
    {"name": "HellFire Staff Reb+2", "max_price": 220000000, "item_ids": ["e89b450b"]},
    {"name": "HellFire Staff Reb+3", "max_price": 220000000, "item_ids": ["e99b450b"]},
    {"name": "HellFire Staff Reb+4", "max_price": 220000000, "item_ids": ["ea9b450b"]},
    {"name": "HellFire Staff Reb+5", "max_price": 220000000, "item_ids": ["eb9b450b"]},
    {"name": "HellFire Staff Reb+6", "max_price": 4000000000, "item_ids": ["ec9b450b"]},
    {"name": "HellFire Staff Reb+7", "max_price": 4500000000, "item_ids": ["ed9b450b"]},
    {"name": "HellFire Staff Reb+8", "max_price": 5000000000, "item_ids": ["ee9b450b"]},
    {"name": "HellFire Staff Reb+9", "max_price": 5000000000, "item_ids": ["ef9b450b"]},
    {"name": "HellFire Staff Reb+10", "max_price": 5000000000, "item_ids": ["f09b450b"]},
    {"name": "HellFire Staff Reb+11", "max_price": 5000000000, "item_ids": ["f19b450b"]},
    {"name": "HellFire Staff Reb+12", "max_price": 5000000000, "item_ids": ["f29b450b"]},
    {"name": "HellFire Staff Reb+13", "max_price": 5000000000, "item_ids": ["f39b450b"]},
    {"name": "HellFire Staff Reb+14", "max_price": 5000000000, "item_ids": ["f49b450b"]},
    {"name": "HellFire Staff Reb+15", "max_price": 5000000000, "item_ids": ["f59b450b"]},
    {"name": "HellFire Staff Reb+16", "max_price": 5000000000, "item_ids": ["f69b450b"]},
    {"name": "HellFire Staff Reb+17", "max_price": 5000000000, "item_ids": ["f79b450b"]},
    {"name": "HellFire Staff Reb+18", "max_price": 5000000000, "item_ids": ["f89b450b"]},
    {"name": "HellFire Staff Reb+19", "max_price": 5000000000, "item_ids": ["f99b450b"]},
    {"name": "HellFire Staff Reb+20", "max_price": 5000000000, "item_ids": ["fa9b450b"]},
    {"name": "HellFire Staff Reb+21", "max_price": 5000000000, "item_ids": ["fb9b450b"]},
    {"name": "Wrath's Spear +0", "max_price": 30000000, "item_ids": ["a7c27e09"]},
    {"name": "Wrath's Spear +1", "max_price": 30000000, "item_ids": ["0bc37e09"]},
    {"name": "Wrath's Spear +2", "max_price": 30000000, "item_ids": ["0cc37e09"]},
    {"name": "Wrath's Spear +3", "max_price": 30000000, "item_ids": ["0dc37e09"]},
    {"name": "Wrath's Spear +4", "max_price": 30000000, "item_ids": ["0ec37e09"]},
    {"name": "Wrath's Spear +5", "max_price": 100000000, "item_ids": ["0fc37e09"]},
    {"name": "Wrath's Spear +6", "max_price": 220000000, "item_ids": ["10c37e09"]},
    {"name": "Wrath's Spear +7", "max_price": 220000000, "item_ids": ["11c37e09"]},
    {"name": "Wrath's Spear +8", "max_price": 220000000, "item_ids": ["12c37e09"]},
    {"name": "Wrath's Spear Reb+1", "max_price": 220000000, "item_ids": ["f9e87e09"]},
    {"name": "Wrath's Spear Reb+2", "max_price": 220000000, "item_ids": ["fae87e09"]},
    {"name": "Wrath's Spear Reb+3", "max_price": 220000000, "item_ids": ["fbe87e09"]},
    {"name": "Wrath's Spear Reb+4", "max_price": 220000000, "item_ids": ["fce87e09"]},
    {"name": "Wrath's Spear Reb+5", "max_price": 220000000, "item_ids": ["fde87e09"]},
    {"name": "Wrath's Spear Reb+6", "max_price": 300000000, "item_ids": ["fee87e09"]},
    {"name": "Wrath's Spear Reb+7", "max_price": 370000000, "item_ids": ["ffe87e09"]},
    {"name": "Wrath's Spear Reb+8", "max_price": 460000000, "item_ids": ["00e87e09"]},
    {"name": "Wrath's Spear Reb+9", "max_price": 5000000000, "item_ids": ["01e87e09"]},
    {"name": "Wrath's Spear Reb+10", "max_price": 5000000000, "item_ids": ["02e87e09"]},
    {"name": "Wrath's Spear Reb+11", "max_price": 5000000000, "item_ids": ["03e87e09"]},
    {"name": "Wrath's Spear Reb+12", "max_price": 5000000000, "item_ids": ["04e87e09"]},
    {"name": "Wrath's Spear Reb+13", "max_price": 5000000000, "item_ids": ["05e87e09"]},
    {"name": "Wrath's Spear Reb+14", "max_price": 5000000000, "item_ids": ["06e87e09"]},
    {"name": "Wrath's Spear Reb+15", "max_price": 5000000000, "item_ids": ["07e87e09"]},
    {"name": "Wrath's Spear Reb+16", "max_price": 5000000000, "item_ids": ["08e87e09"]},
    {"name": "Wrath's Spear Reb+17", "max_price": 5000000000, "item_ids": ["09e87e09"]},
    {"name": "Wrath's Spear Reb+18", "max_price": 5000000000, "item_ids": ["0ae87e09"]},
    {"name": "Wrath's Spear Reb+19", "max_price": 5000000000, "item_ids": ["0be87e09"]},
    {"name": "Wrath's Spear Reb+20", "max_price": 5000000000, "item_ids": ["0ce87e09"]},
    {"name": "Wrath's Spear Reb+21", "max_price": 5000000000, "item_ids": ["0de87e09"]},
    {"name": "Hope's Fire Staff +0", "max_price": 220000000, "item_ids": []},
    {"name": "Hope's Fire Staff +1", "max_price": 20000000, "item_ids": ["6787480b"]},
    {"name": "Hope's Fire Staff +2", "max_price": 20000000, "item_ids": ["6887480b"]},
    {"name": "Hope's Fire Staff +3", "max_price": 20000000, "item_ids": ["6987480b"]},
    {"name": "Hope's Fire Staff +4", "max_price": 20000000, "item_ids": ["6a87480b"]},
    {"name": "Hope's Fire Staff +5", "max_price": 20000000, "item_ids": ["6b87480b"]},
    {"name": "Hope's Fire Staff +6", "max_price": 20000000, "item_ids": ["6c87480b"]},
    {"name": "Hope's Fire Staff +7", "max_price": 220000000, "item_ids": ["6d87480b"]},
    {"name": "Hope's Fire Staff +8", "max_price": 220000000, "item_ids": ["6e87480b"]},
    {"name": "Hope's Fire Staff +9", "max_price": 10000000000, "item_ids": ["6f87480b"]},
    {"name": "Hope's Fire Staff +10", "max_price": 10000000000, "item_ids": ["7087480b"]},
    {"name": "Dark Shadow Dagger +0", "max_price": 40000000, "item_ids": ["ad561907"]},
    {"name": "Dark Shadow Dagger +1", "max_price": 40000000, "item_ids": ["11571907"]},
    {"name": "Dark Shadow Dagger +2", "max_price": 40000000, "item_ids": ["12571907"]},
    {"name": "Dark Shadow Dagger +3", "max_price": 40000000, "item_ids": ["13571907"]},
    {"name": "Dark Shadow Dagger +4", "max_price": 40000000, "item_ids": ["14571907"]},
    {"name": "Dark Shadow Dagger +5", "max_price": 60000000, "item_ids": ["15571907"]},
    {"name": "Dark Shadow Dagger +6", "max_price": 100000000, "item_ids": ["16571907"]},
    {"name": "Dark Shadow Dagger +7", "max_price": 220000000, "item_ids": ["17571907"]},
    {"name": "Dark Shadow Dagger +8", "max_price": 220000000, "item_ids": ["18571907"]},
    {"name": "Dark Shadow Dagger Reb+1", "max_price": 220000000, "item_ids": ["d17d1907"]},
    {"name": "Dark Shadow Dagger Reb+2", "max_price": 220000000, "item_ids": ["d27d1907"]},
    {"name": "Dark Shadow Dagger Reb+3", "max_price": 220000000, "item_ids": ["d37d1907"]},
    {"name": "Dark Shadow Dagger Reb+4", "max_price": 220000000, "item_ids": ["d47d1907"]},
    {"name": "Dark Shadow Dagger Reb+5", "max_price": 220000000, "item_ids": ["d57d1907"]},
    {"name": "Dark Shadow Dagger Reb+6", "max_price": 4700000000, "item_ids": ["d67d1907"]},
    {"name": "Dark Shadow Dagger Reb+7", "max_price": 5000000000, "item_ids": ["d77d1907"]},
    {"name": "Dark Shadow Dagger Reb+8", "max_price": 5000000000, "item_ids": ["d87d1907"]},
    {"name": "Dark Shadow Dagger Reb+9", "max_price": 5000000000, "item_ids": ["d97d1907"]},
    {"name": "Dark Shadow Dagger Reb+10", "max_price": 5000000000, "item_ids": ["da7d1907"]},
    {"name": "Dark Shadow Dagger Reb+11", "max_price": 5000000000, "item_ids": ["db7d1907"]},
    {"name": "Dark Shadow Dagger Reb+12", "max_price": 5000000000, "item_ids": ["dc7d1907"]},
    {"name": "Dark Shadow Dagger Reb+13", "max_price": 5000000000, "item_ids": ["dd7d1907"]},
    {"name": "Dark Shadow Dagger Reb+14", "max_price": 5000000000, "item_ids": ["de7d1907"]},
    {"name": "Dark Shadow Dagger Reb+15", "max_price": 5000000000, "item_ids": ["df7d1907"]},
    {"name": "Dark Shadow Dagger Reb+16", "max_price": 5000000000, "item_ids": ["e07d1907"]},
    {"name": "Dark Shadow Dagger Reb+17", "max_price": 5000000000, "item_ids": ["e17d1907"]},
    {"name": "Dark Shadow Dagger Reb+18", "max_price": 5000000000, "item_ids": ["e27d1907"]},
    {"name": "Dark Shadow Dagger Reb+19", "max_price": 5000000000, "item_ids": ["e37d1907"]},
    {"name": "Dark Shadow Dagger Reb+20", "max_price": 5000000000, "item_ids": ["e47d1907"]},
    {"name": "Dark Shadow Dagger Reb+21", "max_price": 5000000000, "item_ids": ["e57d1907"]},
    {"name": "Starlight Staff +8", "max_price": 400000000, "item_ids": ["c8084a0b"]},
    {"name": "Starlight Staff +9", "max_price": 5000000000, "item_ids": ["c9084a0b"]},
    {"name": "Starlight Staff +10", "max_price": 5000000000, "item_ids": ["ca084a0b"]},
    {"name": "Dragon Wing Bow +0", "max_price": 220000000, "item_ids": ["4959170a"]},
    {"name": "Dragon Wing Bow +1", "max_price": 220000000, "item_ids": ["8b59170a"]},
    {"name": "Dragon Wing Bow +2", "max_price": 220000000, "item_ids": ["8c59170a"]},
    {"name": "Dragon Wing Bow +3", "max_price": 220000000, "item_ids": ["8d59170a"]},
    {"name": "Dragon Wing Bow +4", "max_price": 220000000, "item_ids": ["8e59170a"]},
    {"name": "Dragon Wing Bow +5", "max_price": 220000000, "item_ids": ["8f59170a"]},
    {"name": "Dragon Wing Bow +6", "max_price": 220000000, "item_ids": ["9059170a"]},
    {"name": "Dragon Wing Bow +7", "max_price": 220000000, "item_ids": ["9159170a"]},
    {"name": "Dragon Wing Bow +8", "max_price": 220000000, "item_ids": ["9259170a", "5159170a"]},
    {"name": "Dragon Wing Bow +9", "max_price": 5000000000, "item_ids": ["9359170a"]},
    {"name": "Dragon Wing Bow +10", "max_price": 5000000000, "item_ids": ["9459170a"]},
    {"name": "Dragon Wing Bow Reb+1", "max_price": 2200000000, "item_ids": ["2d80170a"]},
    {"name": "Dragon Wing Bow Reb+2", "max_price": 2200000000, "item_ids": ["2e80170a"]},
    {"name": "Dragon Wing Bow Reb+3", "max_price": 2200000000, "item_ids": ["2f80170a"]},
    {"name": "Dragon Wing Bow Reb+4", "max_price": 2200000000, "item_ids": ["3080170a"]},
    {"name": "Dragon Wing Bow Reb+5", "max_price": 3000000000, "item_ids": ["3180170a"]},
    {"name": "Dragon Wing Bow Reb+6", "max_price": 3000000000, "item_ids": ["3280170a"]},
    {"name": "Dragon Wing Bow Reb+7", "max_price": 4000000000, "item_ids": ["3380170a"]},
    {"name": "Dragon Wing Bow Reb+8", "max_price": 5000000000, "item_ids": ["3480170a"]},
    {"name": "Dragon Wing Bow Reb+9", "max_price": 5000000000, "item_ids": ["3580170a"]},
    {"name": "Dragon Wing Bow Reb+10", "max_price": 5000000000, "item_ids": ["3680170a"]},
    {"name": "Dragon Wing Bow Reb+11", "max_price": 10000000000, "item_ids": ["3780170a"]},
    {"name": "Dragon Wing Bow Reb+12", "max_price": 10000000000, "item_ids": ["3880170a"]},
    {"name": "Dragon Wing Bow Reb+13", "max_price": 10000000000, "item_ids": ["3980170a"]},
    {"name": "Dragon Wing Bow Reb+14", "max_price": 10000000000, "item_ids": ["3a80170a"]},
    {"name": "Dragon Wing Bow Reb+15", "max_price": 10000000000, "item_ids": ["3b80170a"]},
    {"name": "Dragon Wing Bow Reb+16", "max_price": 10000000000, "item_ids": ["3c80170a"]},
    {"name": "Dragon Wing Bow Reb+17", "max_price": 10000000000, "item_ids": ["3d80170a"]},
    {"name": "Dragon Wing Bow Reb+18", "max_price": 10000000000, "item_ids": ["3e80170a"]},
    {"name": "Dragon Wing Bow Reb+19", "max_price": 10000000000, "item_ids": ["3f80170a"]},
    {"name": "Dragon Wing Bow Reb+20", "max_price": 10000000000, "item_ids": ["4080170a"]},
    {"name": "Dragon Wing Bow Reb+21", "max_price": 10000000000, "item_ids": ["4180170a"]},
    {"name": "Hope's Thunder Staff +7", "max_price": 50000000, "item_ids": ["e100470b"]},
    {"name": "Hope's Thunder Staff +8", "max_price": 500000000, "item_ids": ["e200470b"]},
    {"name": "Hope's Thunder Staff +9", "max_price": 5000000000, "item_ids": ["e300470b"]},
    {"name": "Hope's Thunder Staff +10", "max_price": 5000000000, "item_ids": ["e400470b"]},
    {"name": "Hope's Thunder Staff Reb+1", "max_price": 50000000, "item_ids": ["f527470b"]},
    {"name": "Hope's Thunder Staff Reb+2", "max_price": 50000000, "item_ids": ["f627470b"]},
    {"name": "Hope's Thunder Staff Reb+3", "max_price": 100000000, "item_ids": ["f727470b"]},
    {"name": "Hope's Thunder Staff Reb+4", "max_price": 200000000, "item_ids": ["f827470b"]},
    {"name": "Hope's Thunder Staff Reb+5", "max_price": 250000000, "item_ids": ["f927470b"]},
    {"name": "Hope's Thunder Staff Reb+6", "max_price": 300000000, "item_ids": ["fa27470b"]},
    {"name": "Hope's Thunder Staff Reb+7", "max_price": 350000000, "item_ids": ["fb27470b"]},
    {"name": "Hope's Thunder Staff Reb+8", "max_price": 400000000, "item_ids": ["fc27470b"]},
    {"name": "Hope's Thunder Staff Reb+9", "max_price": 450000000, "item_ids": ["fd27470b"]},
    {"name": "Hope's Thunder Staff Reb+10", "max_price": 5000000000, "item_ids": ["fe27470b"]},
    {"name": "Hope's Thunder Staff Reb+11", "max_price": 5000000000, "item_ids": ["ff27470b"]},
    {"name": "Hope's Thunder Staff Reb+12", "max_price": 5000000000, "item_ids": ["0027470b"]},
    {"name": "Hope's Thunder Staff Reb+13", "max_price": 5000000000, "item_ids": ["0127470b"]},
    {"name": "Hope's Thunder Staff Reb+14", "max_price": 5000000000, "item_ids": ["0227470b"]},
    {"name": "Hope's Thunder Staff Reb+15", "max_price": 5000000000, "item_ids": ["0327470b"]},
    {"name": "Hope's Thunder Staff Reb+16", "max_price": 5000000000, "item_ids": ["0427470b"]},
    {"name": "Hope's Thunder Staff Reb+17", "max_price": 5000000000, "item_ids": ["0527470b"]},
    {"name": "Hope's Thunder Staff Reb+18", "max_price": 5000000000, "item_ids": ["0627470b"]},
    {"name": "Hope's Thunder Staff Reb+19", "max_price": 5000000000, "item_ids": ["0727470b"]},
    {"name": "Hope's Thunder Staff Reb+20", "max_price": 5000000000, "item_ids": ["0827470b"]},
    {"name": "Hope's Thunder Staff Reb+21", "max_price": 5000000000, "item_ids": ["0927470b"]},
    {"name": "Thunder Animor +1", "max_price": 20000000, "item_ids": ["c319e10b"]},
    {"name": "Thunder Animor +2", "max_price": 20000000, "item_ids": ["c419e10b"]},
    {"name": "Thunder Animor +3", "max_price": 20000000, "item_ids": ["c519e10b"]},
    {"name": "Thunder Animor +4", "max_price": 40000000, "item_ids": ["c619e10b"]},
    {"name": "Thunder Animor +5", "max_price": 50000000, "item_ids": ["c719e10b"]},
    {"name": "Thunder Animor +6", "max_price": 100000000, "item_ids": ["c819e10b"]},
    {"name": "Thunder Animor +7", "max_price": 220000000, "item_ids": ["c919e10b"]},
    {"name": "Thunder Animor +8", "max_price": 220000000, "item_ids": ["ca19e10b"]},
    {"name": "Thunder Animor Reb+1", "max_price": 220000000, "item_ids": ["a73fe10b"]},
    {"name": "Thunder Animor Reb+2", "max_price": 220000000, "item_ids": ["a83fe10b"]},
    {"name": "Thunder Animor Reb+3", "max_price": 220000000, "item_ids": ["a93fe10b"]},
    {"name": "Thunder Animor Reb+4", "max_price": 220000000, "item_ids": ["aa3fe10b"]},
    {"name": "Thunder Animor Reb+5", "max_price": 220000000, "item_ids": ["ab3fe10b"]},
    {"name": "Thunder Animor Reb+6", "max_price": 220000000, "item_ids": ["ac3fe10b"]},
    {"name": "Thunder Animor Reb+7", "max_price": 220000000, "item_ids": ["ad3fe10b"]},
    {"name": "Thunder Animor Reb+8", "max_price": 250000000, "item_ids": ["ae3fe10b"]},
    {"name": "Thunder Animor Reb+9", "max_price": 1000000000, "item_ids": ["af3fe10b"]},
    {"name": "Thunder Animor Reb+10", "max_price": 1000000000, "item_ids": ["b03fe10b"]},
    {"name": "Thunder Animor Reb+11", "max_price": 5000000000, "item_ids": ["b13fe10b"]},
    {"name": "Thunder Animor Reb+12", "max_price": 5000000000, "item_ids": ["b23fe10b"]},
    {"name": "Thunder Animor Reb+13", "max_price": 5000000000, "item_ids": ["b33fe10b"]},
    {"name": "Thunder Animor Reb+14", "max_price": 5000000000, "item_ids": ["b43fe10b"]},
    {"name": "Thunder Animor Reb+15", "max_price": 5000000000, "item_ids": ["b53fe10b"]},
    {"name": "Thunder Animor Reb+16", "max_price": 50000000000, "item_ids": ["b63fe10b"]},
    {"name": "Thunder Animor Reb+17", "max_price": 5000000000, "item_ids": ["b73fe10b"]},
    {"name": "Thunder Animor Reb+18", "max_price": 5000000000, "item_ids": ["b83fe10b"]},
    {"name": "Thunder Animor Reb+19", "max_price": 5000000000, "item_ids": ["b93fe10b"]},
    {"name": "Thunder Animor Reb+20", "max_price": 5000000000, "item_ids": ["ba3fe10b"]},
    {"name": "Thunder Animor Reb+21", "max_price": 5000000000, "item_ids": ["bb3fe10b"]},
    {"name": "Firelance +1", "max_price": 10000000, "item_ids": ["87bf7e09"]},
    {"name": "Firelance +2", "max_price": 10000000, "item_ids": ["88bf7e09"]},
    {"name": "Firelance +3", "max_price": 10000000, "item_ids": ["89bf7e09"]},
    {"name": "Firelance +4", "max_price": 15555555, "item_ids": ["8abf7e09"]},
    {"name": "Firelance +5", "max_price": 20000000, "item_ids": ["8bbf7e09"]},
    {"name": "Firelance +6", "max_price": 40000000, "item_ids": ["8cbf7e09"]},
    {"name": "Firelance +7", "max_price": 180000000, "item_ids": ["8dbf7e09"]},
    {"name": "Firelance +8", "max_price": 220000000, "item_ids": ["8ebf7e09"]},
    {"name": "Firelance +9", "max_price": 5000000000, "item_ids": ["8fbf7e09"]},
    {"name": "Firelance +10", "max_price": 5000000000, "item_ids": ["90bf7e09"]},
    {"name": "Firelance Reb+1", "max_price": 180000000, "item_ids": ["f3e47e09"]},
    {"name": "Firelance Reb+2", "max_price": 180000000, "item_ids": ["f4e47e09"]},
    {"name": "Firelance Reb+3", "max_price": 220000000, "item_ids": ["f5e47e09"]},
    {"name": "Firelance Reb+4", "max_price": 220000000, "item_ids": ["f6e47e09"]},
    {"name": "Firelance Reb+5", "max_price": 350000000, "item_ids": ["f7e47e09"]},
    {"name": "Firelance Reb+6", "max_price": 400000000, "item_ids": ["f8e47e09"]},
    {"name": "Firelance Reb+7", "max_price": 400000000, "item_ids": ["f9e47e09"]},
    {"name": "Firelance Reb+8", "max_price": 500000000, "item_ids": ["fae47e09"]},
    {"name": "Firelance Reb+9", "max_price": 500000000, "item_ids": ["fbe47e09"]},
    {"name": "Firelance Reb+10", "max_price": 5000000000, "item_ids": ["fce47e09"]},
    {"name": "Firelance Reb+11", "max_price": 5000000000, "item_ids": ["fde47e09"]},
    {"name": "Firelance Reb+12", "max_price": 5000000000, "item_ids": ["fee47e09"]},
    {"name": "Firelance Reb+13", "max_price": 5000000000, "item_ids": ["ffe47e09"]},
    {"name": "Firelance Reb+14", "max_price": 5000000000, "item_ids": ["00e47e09"]},
    {"name": "Firelance Reb+15", "max_price": 5000000000, "item_ids": ["01e47e09"]},
    {"name": "Firelance Reb+16", "max_price": 5000000000, "item_ids": ["02e47e09"]},
    {"name": "Firelance Reb+17", "max_price": 5000000000, "item_ids": ["03e47e09"]},
    {"name": "Firelance Reb+18", "max_price": 5000000000, "item_ids": ["04e47e09"]},
    {"name": "Firelance Reb+19", "max_price": 5000000000, "item_ids": ["05e47e09"]},
    {"name": "Firelance Reb+20", "max_price": 5000000000, "item_ids": ["06e47e09"]},
    {"name": "Firelance Reb+21", "max_price": 5000000000, "item_ids": ["07e47e09"]},
    {"name": "Frozendeath Dagger +0", "max_price": 220000000, "item_ids": ["0b641c07"]},
    {"name": "Frozendeath Dagger +1", "max_price": 220000000, "item_ids": ["7d651c07"]},
    {"name": "Frozendeath Dagger +2", "max_price": 220000000, "item_ids": ["7e651c07"]},
    {"name": "Frozendeath Dagger +3", "max_price": 220000000, "item_ids": ["7f651c07"]},
    {"name": "Frozendeath Dagger +4", "max_price": 220000000, "item_ids": ["80651c07"]},
    {"name": "Frozendeath Dagger +5", "max_price": 220000000, "item_ids": ["81651c07"]},
    {"name": "Frozendeath Dagger +6", "max_price": 220000000, "item_ids": ["82651c07"]},
    {"name": "Frozendeath Dagger +7", "max_price": 220000000, "item_ids": ["83651c07"]},
    {"name": "Frozendeath Dagger +8", "max_price": 220000000, "item_ids": ["84651c07"]},
    {"name": "Frozendeath Dagger +9", "max_price": 5000000000, "item_ids": ["85651c07"]},
    {"name": "Frozendeath Dagger +10", "max_price": 5000000000, "item_ids": ["86651c07"]},
    {"name": "Frozendeath Dagger Reb+1", "max_price": 500000000, "item_ids": ["2f8b1c07"]},
    {"name": "Frozendeath Dagger Reb+2", "max_price": 500000000, "item_ids": ["308b1c07"]},
    {"name": "Frozendeath Dagger Reb+3", "max_price": 800000000, "item_ids": ["318b1c07"]},
    {"name": "Frozendeath Dagger Reb+4", "max_price": 1200000000, "item_ids": ["328b1c07"]},
    {"name": "Frozendeath Dagger Reb+5", "max_price": 3000000000, "item_ids": ["338b1c07"]},
    {"name": "Frozendeath Dagger Reb+6", "max_price": 3000000000, "item_ids": ["348b1c07"]},
    {"name": "Frozendeath Dagger Reb+7", "max_price": 5000000000, "item_ids": ["358b1c07"]},
    {"name": "Frozendeath Dagger Reb+8", "max_price": 5000000000, "item_ids": ["368b1c07"]},
    {"name": "Frozendeath Dagger Reb+9", "max_price": 5000000000, "item_ids": ["378b1c07"]},
    {"name": "Frozendeath Dagger Reb+10", "max_price": 5000000000, "item_ids": ["388b1c07"]},
    {"name": "Frozendeath Dagger Reb+11", "max_price": 10000000000, "item_ids": ["398b1c07"]},
    {"name": "Frozendeath Dagger Reb+12", "max_price": 10000000000, "item_ids": ["3a8b1c07"]},
    {"name": "Frozendeath Dagger Reb+13", "max_price": 10000000000, "item_ids": ["3b8b1c07"]},
    {"name": "Frozendeath Dagger Reb+14", "max_price": 10000000000, "item_ids": ["3c8b1c07"]},
    {"name": "Frozendeath Dagger Reb+15", "max_price": 10000000000, "item_ids": ["3d8b1c07"]},
    {"name": "Frozendeath Dagger Reb+16", "max_price": 10000000000, "item_ids": ["3e8b1c07"]},
    {"name": "Frozendeath Dagger Reb+17", "max_price": 10000000000, "item_ids": ["3f8b1c07"]},
    {"name": "Frozendeath Dagger Reb+18", "max_price": 10000000000, "item_ids": ["408b1c07"]},
    {"name": "Frozendeath Dagger Reb+19", "max_price": 10000000000, "item_ids": ["418b1c07"]},
    {"name": "Frozendeath Dagger Reb+20", "max_price": 10000000000, "item_ids": ["428b1c07"]},
    {"name": "Frozendeath Dagger Reb+21", "max_price": 10000000000, "item_ids": ["438b1c07"]},
    {"name": "Frozen Cross Bow +0", "max_price": 100000000, "item_ids": ["8e54170a"]},
    {"name": "Frozen Cross Bow +1", "max_price": 100000000, "item_ids": ["1b56170a"]},
    {"name": "Frozen Cross Bow +2", "max_price": 100000000, "item_ids": ["1c56170a"]},
    {"name": "Frozen Cross Bow +3", "max_price": 100000000, "item_ids": ["1d56170a"]},
    {"name": "Frozen Cross Bow +4", "max_price": 100000000, "item_ids": ["1e56170a"]},
    {"name": "Frozen Cross Bow +5", "max_price": 100000000, "item_ids": ["1f56170a"]},
    {"name": "Frozen Cross Bow +6", "max_price": 220000000, "item_ids": ["2056170a"]},
    {"name": "Frozen Cross Bow +7", "max_price": 220000000, "item_ids": ["2156170a"]},
    {"name": "Frozen Cross Bow +8", "max_price": 220000000, "item_ids": ["2256170a"]},
    {"name": "Frozen Cross Bow +9", "max_price": 5000000000, "item_ids": ["2356170a"]},
    {"name": "Frozen Cross Bow +10", "max_price": 5000000000, "item_ids": ["2456170a"]},
    {"name": "Frozen Cross Bow Reb+1", "max_price": 220000000, "item_ids": ["cd7b170a"]},
    {"name": "Frozen Cross Bow Reb+2", "max_price": 220000000, "item_ids": ["ce7b170a"]},
    {"name": "Frozen Cross Bow Reb+3", "max_price": 550000000, "item_ids": ["cf7b170a"]},
    {"name": "Frozen Cross Bow Reb+4", "max_price": 1000000000, "item_ids": ["d07b170a"]},
    {"name": "Frozen Cross Bow Reb+5", "max_price": 4000000000, "item_ids": ["d17b170a"]},
    {"name": "Frozen Cross Bow Reb+6", "max_price": 5000000000, "item_ids": ["d27b170a"]},
    {"name": "Frozen Cross Bow Reb+7", "max_price": 5000000000, "item_ids": ["d37b170a"]},
    {"name": "Frozen Cross Bow Reb+8", "max_price": 5000000000, "item_ids": ["d47b170a"]},
    {"name": "Frozen Cross Bow Reb+9", "max_price": 5000000000, "item_ids": ["d57b170a"]},
    {"name": "Frozen Cross Bow Reb+10", "max_price": 5000000000, "item_ids": ["d67b170a"]},
    {"name": "Frozen Cross Bow Reb+11", "max_price": 5000000000, "item_ids": ["d77b170a"]},
    {"name": "Frozen Cross Bow Reb+12", "max_price": 5000000000, "item_ids": ["d87b170a"]},
    {"name": "Frozen Cross Bow Reb+13", "max_price": 5000000000, "item_ids": ["d97b170a"]},
    {"name": "Frozen Cross Bow Reb+14", "max_price": 5000000000, "item_ids": ["da7b170a"]},
    {"name": "Frozen Cross Bow Reb+15", "max_price": 5000000000, "item_ids": ["db7b170a"]},
    {"name": "Frozen Cross Bow Reb+16", "max_price": 5000000000, "item_ids": ["dc7b170a"]},
    {"name": "Frozen Cross Bow Reb+17", "max_price": 5000000000, "item_ids": ["dd7b170a"]},
    {"name": "Frozen Cross Bow Reb+18", "max_price": 5000000000, "item_ids": ["de7b170a"]},
    {"name": "Frozen Cross Bow Reb+19", "max_price": 5000000000, "item_ids": ["df7b170a"]},
    {"name": "Frozen Cross Bow Reb+20", "max_price": 5000000000, "item_ids": ["e07b170a"]},
    {"name": "Frozen Cross Bow Reb+21", "max_price": 5000000000, "item_ids": ["e17b170a"]},
    {"name": "Gaze of Icedeath +6", "max_price": 25000000, "item_ids": ["fc1a4d0b"]},
    {"name": "Gaze of Icedeath +7", "max_price": 50000000, "item_ids": ["fd1a4d0b"]},
    {"name": "Gaze of Icedeath +8", "max_price": 250000000, "item_ids": ["fe1a4d0b"]},
    {"name": "Gaze of Icedeath +9", "max_price": 5000000000, "item_ids": ["ff1a4d0b"]},
    {"name": "Gaze of Icedeath +10", "max_price": 5000000000, "item_ids": ["001a4d0b"]},
    {"name": "King Axe +0", "max_price": 10000000, "item_ids": ["73621708"]},
    {"name": "King Axe +1", "max_price": 15000000, "item_ids": ["7f621708"]},
    {"name": "King Axe +2", "max_price": 15000000, "item_ids": ["80621708"]},
    {"name": "King Axe +3", "max_price": 15000000, "item_ids": ["81621708"]},
    {"name": "King Axe +4", "max_price": 20000000, "item_ids": ["82621708"]},
    {"name": "King Axe +5", "max_price": 50000000, "item_ids": ["83621708"]},
    {"name": "King Axe +6", "max_price": 100000000, "item_ids": ["84621708"]},
    {"name": "King Axe +7", "max_price": 100000000, "item_ids": ["85621708"]},
    {"name": "King Axe +8", "max_price": 220000000, "item_ids": ["86621708"]},
    {"name": "King Axe +9", "max_price": 5000000000, "item_ids": ["87621708"]},
    {"name": "King Axe +10", "max_price": 5000000000, "item_ids": ["88621708"]},
    {"name": "HellFire Bow +0", "max_price": 40000000, "item_ids": ["cf469009"]},
    {"name": "HellFire Bow +1", "max_price": 100000000, "item_ids": ["df469009"]},
    {"name": "HellFire Bow +2", "max_price": 100000000, "item_ids": ["e0469009"]},
    {"name": "HellFire Bow +3", "max_price": 100000000, "item_ids": ["e1469009"]},
    {"name": "HellFire Bow +4", "max_price": 100000000, "item_ids": ["e2469009"]},
    {"name": "HellFire Bow +5", "max_price": 100000000, "item_ids": ["e3469009"]},
    {"name": "HellFire Bow +6", "max_price": 220000000, "item_ids": ["e4469009"]},
    {"name": "HellFire Bow +7", "max_price": 220000000, "item_ids": ["e5469009"]},
    {"name": "HellFire Bow +8", "max_price": 220000000, "item_ids": ["e6469009"]},
    {"name": "HellFire Bow +9", "max_price": 5000000000, "item_ids": ["e7469009"]},
    {"name": "HellFire Bow +10", "max_price": 5000000000, "item_ids": ["e8469009"]},
    {"name": "Venom Hammer +1", "max_price": 10000000, "item_ids": ["1ffd560b"]},
    {"name": "Venom Hammer +2", "max_price": 10000000, "item_ids": ["20fd560b"]},
    {"name": "Venom Hammer +3", "max_price": 10000000, "item_ids": ["21fd560b"]},
    {"name": "Venom Hammer +4", "max_price": 15000000, "item_ids": ["22fd560b"]},
    {"name": "Venom Hammer +5", "max_price": 20000000, "item_ids": ["23fd560b"]},
    {"name": "Venom Hammer +6", "max_price": 120000000, "item_ids": ["24fd560b"]},
    {"name": "Venom Hammer +7", "max_price": 220000000, "item_ids": ["25fd560b"]},
    {"name": "Venom Hammer +8", "max_price": 220000000, "item_ids": ["26fd560b"]},
    {"name": "Venom Hammer +9", "max_price": 5000000000, "item_ids": ["27fd560b"]},
    {"name": "Venom Hammer +10", "max_price": 5000000000, "item_ids": ["28fd560b"]},
    {"name": "Claw Hammer +0", "max_price": 10000000, "item_ids": ["0dfd560b"]},
    {"name": "Claw Hammer +1", "max_price": 10000000, "item_ids": ["33fd560b"]},
    {"name": "Claw Hammer +2", "max_price": 10000000, "item_ids": ["34fd560b"]},
    {"name": "Claw Hammer +3", "max_price": 15000000, "item_ids": ["35fd560b"]},
    {"name": "Claw Hammer +4", "max_price": 20000000, "item_ids": ["36fd560b"]},
    {"name": "Claw Hammer +5", "max_price": 20000000, "item_ids": ["37fd560b"]},
    {"name": "Claw Hammer +6", "max_price": 40000000, "item_ids": ["38fd560b"]},
    {"name": "Claw Hammer +7", "max_price": 100000000, "item_ids": ["39fd560b"]},
    {"name": "Claw Hammer +8", "max_price": 220000000, "item_ids": ["3afd560b"]},
    {"name": "Claw Hammer Reb+1", "max_price": 100000000, "item_ids": ["7100570b"]},
    {"name": "Claw Hammer Reb+2", "max_price": 220000000, "item_ids": ["7200570b"]},
    {"name": "Claw Hammer Reb+3", "max_price": 220000000, "item_ids": ["7300570b"]},
    {"name": "Claw Hammer Reb+4", "max_price": 220000000, "item_ids": ["7400570b"]},
    {"name": "Claw Hammer Reb+5", "max_price": 220000000, "item_ids": ["7500570b"]},
    {"name": "Claw Hammer Reb+6", "max_price": 300000000, "item_ids": ["7600570b"]},
    {"name": "Claw Hammer Reb+7", "max_price": 400000000, "item_ids": ["7700570b"]},
    {"name": "Claw Hammer Reb+8", "max_price": 500000000, "item_ids": ["7800570b"]},
    {"name": "Claw Hammer Reb+9", "max_price": 1000000000, "item_ids": ["7900570b"]},
    {"name": "Claw Hammer Reb+10", "max_price": 3000000000, "item_ids": ["7a00570b"]},
    {"name": "Claw Hammer Reb+11", "max_price": 5000000000, "item_ids": ["7b00570b"]},
    {"name": "Claw Hammer Reb+12", "max_price": 5000000000, "item_ids": ["7c00570b"]},
    {"name": "Claw Hammer Reb+13", "max_price": 5000000000, "item_ids": ["7d00570b"]},
    {"name": "Claw Hammer Reb+14", "max_price": 5000000000, "item_ids": ["7e00570b"]},
    {"name": "Claw Hammer Reb+15", "max_price": 5000000000, "item_ids": ["7f00570b"]},
    {"name": "Claw Hammer Reb+16", "max_price": 5000000000, "item_ids": ["8000570b"]},
    {"name": "Claw Hammer Reb+17", "max_price": 5000000000, "item_ids": ["8100570b"]},
    {"name": "Claw Hammer Reb+18", "max_price": 5000000000, "item_ids": ["8200570b"]},
    {"name": "Claw Hammer Reb+19", "max_price": 5000000000, "item_ids": ["8300570b"]},
    {"name": "Claw Hammer Reb+20", "max_price": 5000000000, "item_ids": ["8400570b"]},
    {"name": "Claw Hammer Reb+21", "max_price": 5000000000, "item_ids": ["8500570b"]},
    {"name": "Nightfang Hammer +1", "max_price": 10000000, "item_ids": ["29fd560b"]},
    {"name": "Nightfang Hammer +2", "max_price": 10000000, "item_ids": ["2afd560b"]},
    {"name": "Nightfang Hammer +3", "max_price": 10000000, "item_ids": ["2bfd560b"]},
    {"name": "Nightfang Hammer +4", "max_price": 40000000, "item_ids": ["2cfd560b"]},
    {"name": "Nightfang Hammer +5", "max_price": 50000000, "item_ids": ["2dfd560b"]},
    {"name": "Nightfang Hammer +6", "max_price": 100000000, "item_ids": ["2efd560b"]},
    {"name": "Nightfang Hammer +7", "max_price": 120000000, "item_ids": ["2ffd560b"]},
    {"name": "Nightfang Hammer +8", "max_price": 220000000, "item_ids": ["30fd560b"]},
    {"name": "Nightfang Hammer +9", "max_price": 5000000000, "item_ids": ["31fd560b"]},
    {"name": "Nightfang Hammer +10", "max_price": 5000000000, "item_ids": ["32fd560b"]},
    {"name": "Lord's Sentinel Shield +0", "max_price": 50000000, "item_ids": ["b6ddac0a"]},
    {"name": "Lord's Sentinel Shield +1", "max_price": 50000000, "item_ids": ["6bdeac0a"]},
    {"name": "Lord's Sentinel Shield +2", "max_price": 50000000, "item_ids": ["6cdeac0a"]},
    {"name": "Lord's Sentinel Shield +3", "max_price": 50000000, "item_ids": ["6ddeac0a"]},
    {"name": "Lord's Sentinel Shield +4", "max_price": 50000000, "item_ids": ["6edeac0a"]},
    {"name": "Lord's Sentinel Shield +5", "max_price": 50000000, "item_ids": ["6fdeac0a"]},
    {"name": "Lord's Sentinel Shield +6", "max_price": 50000000, "item_ids": ["70deac0a"]},
    {"name": "Lord's Sentinel Shield +7", "max_price": 220000000, "item_ids": ["71deac0a"]},
    {"name": "Lord's Sentinel Shield +8", "max_price": 220000000, "item_ids": ["72deac0a"]},
    {"name": "Lord's Sentinel Shield +9", "max_price": 5000000000, "item_ids": ["73deac0a"]},
    {"name": "Lord's Sentinel Shield +10", "max_price": 5000000000, "item_ids": ["74deac0a"]},
    {"name": "Lord's Sentinel Shield Reb+1", "max_price": 220000000, "item_ids": ["a305ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+2", "max_price": 220000000, "item_ids": ["a405ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+3", "max_price": 220000000, "item_ids": ["a505ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+4", "max_price": 220000000, "item_ids": ["a605ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+5", "max_price": 220000000, "item_ids": ["a705ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+6", "max_price": 3000000000, "item_ids": ["a805ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+7", "max_price": 3000000000, "item_ids": ["a905ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+8", "max_price": 4000000000, "item_ids": ["aa05ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+9", "max_price": 5000000000, "item_ids": ["ab05ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+10", "max_price": 5000000000, "item_ids": ["ac05ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+11", "max_price": 5000000000, "item_ids": ["ad05ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+12", "max_price": 5000000000, "item_ids": ["ae05ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+13", "max_price": 5000000000, "item_ids": ["af05ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+14", "max_price": 5000000000, "item_ids": ["b005ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+15", "max_price": 5000000000, "item_ids": ["b105ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+16", "max_price": 5000000000, "item_ids": ["b205ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+17", "max_price": 5000000000, "item_ids": ["b305ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+18", "max_price": 5000000000, "item_ids": ["b405ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+19", "max_price": 5000000000, "item_ids": ["b505ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+20", "max_price": 5000000000, "item_ids": ["b605ad0a"]},
    {"name": "Lord's Sentinel Shield Reb+21", "max_price": 5000000000, "item_ids": ["b705ad0a"]},
    {"name": "Phantom Shield +0", "max_price": 220000000, "item_ids": ["efe1ac0a"]},
    {"name": "Phantom Shield +1", "max_price": 220000000, "item_ids": ["71e2ac0a", "f0e1ac0a"]},
    {"name": "Phantom Shield +2", "max_price": 220000000, "item_ids": ["72e2ac0a", "f1e1ac0a"]},
    {"name": "Phantom Shield +3", "max_price": 220000000, "item_ids": ["73e2ac0a", "f2e1ac0a"]},
    {"name": "Phantom Shield +4", "max_price": 220000000, "item_ids": ["74e2ac0a", "f3e1ac0a"]},
    {"name": "Phantom Shield +5", "max_price": 220000000, "item_ids": ["75e2ac0a", "f4e1ac0a"]},
    {"name": "Phantom Shield +6", "max_price": 220000000, "item_ids": ["76e2ac0a", "f5e1ac0a"]},
    {"name": "Phantom Shield +7", "max_price": 220000000, "item_ids": ["77e2ac0a", "f6e1ac0a"]},
    {"name": "Phantom Shield +8", "max_price": 220000000, "item_ids": ["78e2ac0a", "f7e1ac0a"]},
    {"name": "Phantom Shield +9", "max_price": 5000000000, "item_ids": ["79e2ac0a", "f8e1ac0a"]},
    {"name": "Phantom Shield +10", "max_price": 5000000000, "item_ids": ["7ae2ac0a", "f9e1ac0a"]},
    {"name": "Phantom Shield Reb+1", "max_price": 220000000, "item_ids": ["ef09ad0a"]},
    {"name": "Phantom Shield Reb+2", "max_price": 220000000, "item_ids": ["f009ad0a"]},
    {"name": "Phantom Shield Reb+3", "max_price": 220000000, "item_ids": ["f109ad0a"]},
    {"name": "Phantom Shield Reb+4", "max_price": 220000000, "item_ids": ["f209ad0a"]},
    {"name": "Phantom Shield Reb+5", "max_price": 220000000, "item_ids": ["f309ad0a"]},
    {"name": "Phantom Shield Reb+6", "max_price": 3000000000, "item_ids": ["f409ad0a"]},
    {"name": "Phantom Shield Reb+7", "max_price": 3000000000, "item_ids": ["f509ad0a"]},
    {"name": "Phantom Shield Reb+8", "max_price": 3500000000, "item_ids": ["f609ad0a"]},
    {"name": "Phantom Shield Reb+9", "max_price": 5000000000, "item_ids": ["f709ad0a"]},
    {"name": "Phantom Shield Reb+10", "max_price": 5000000000, "item_ids": ["f809ad0a"]},
    {"name": "Phantom Shield Reb+11", "max_price": 5000000000, "item_ids": ["f909ad0a"]},
    {"name": "Phantom Shield Reb+12", "max_price": 5000000000, "item_ids": ["fa09ad0a"]},
    {"name": "Phantom Shield Reb+13", "max_price": 5000000000, "item_ids": ["fb09ad0a"]},
    {"name": "Phantom Shield Reb+14", "max_price": 5000000000, "item_ids": ["fc09ad0a"]},
    {"name": "Phantom Shield Reb+15", "max_price": 5000000000, "item_ids": ["fd09ad0a"]},
    {"name": "Phantom Shield Reb+16", "max_price": 5000000000, "item_ids": ["fe09ad0a"]},
    {"name": "Phantom Shield Reb+17", "max_price": 5000000000, "item_ids": ["ff09ad0a"]},
    {"name": "Phantom Shield Reb+18", "max_price": 5000000000, "item_ids": ["0009ad0a"]},
    {"name": "Phantom Shield Reb+19", "max_price": 5000000000, "item_ids": ["0109ad0a"]},
    {"name": "Phantom Shield Reb+20", "max_price": 5000000000, "item_ids": ["0209ad0a"]},
    {"name": "Phantom Shield Reb+21", "max_price": 5000000000, "item_ids": ["0309ad0a"]},
    {"name": "Legendary Shield +0", "max_price": 1000000000, "item_ids": ["10d0250a"]},
    {"name": "Legendary Shield +1", "max_price": 1000000000, "item_ids": ["15d0250a"]},
    {"name": "Legendary Shield +2", "max_price": 1000000000, "item_ids": ["16d0250a"]},
    {"name": "Legendary Shield +3", "max_price": 1000000000, "item_ids": ["17d0250a"]},
    {"name": "Legendary Shield +4", "max_price": 1000000000, "item_ids": ["18d0250a"]},
    {"name": "Legendary Shield +5", "max_price": 1000000000, "item_ids": ["19d0250a"]},
    {"name": "Legendary Shield +6", "max_price": 1000000000, "item_ids": ["1ad0250a"]},
    {"name": "Legendary Shield +7", "max_price": 1000000000, "item_ids": ["1bd0250a"]},
    {"name": "Legendary Shield +8", "max_price": 5000000000, "item_ids": ["1cd0250a"]},
    {"name": "Legendary Shield +9", "max_price": 5000000000, "item_ids": ["1dd0250a"]},
    {"name": "Legendary Shield +10", "max_price": 5000000000, "item_ids": ["1ed0250a"]},
    {"name": "Frozen Axe +0", "max_price": 220000000, "item_ids": ["0d914d08"]},
    {"name": "Frozen Axe +1", "max_price": 220000000, "item_ids": ["91924d08"]},
    {"name": "Frozen Axe +2", "max_price": 220000000, "item_ids": ["92924d08"]},
    {"name": "Frozen Axe +3", "max_price": 220000000, "item_ids": ["93924d08"]},
    {"name": "Frozen Axe +4", "max_price": 220000000, "item_ids": ["94924d08"]},
    {"name": "Frozen Axe +5", "max_price": 220000000, "item_ids": ["95924d08"]},
    {"name": "Frozen Axe +6", "max_price": 220000000, "item_ids": ["96924d08"]},
    {"name": "Frozen Axe +7", "max_price": 220000000, "item_ids": ["97924d08"]},
    {"name": "Frozen Axe +8", "max_price": 220000000, "item_ids": ["98924d08"]},
    {"name": "Frozen Axe +9", "max_price": 5000000000, "item_ids": ["99924d08"]},
    {"name": "Frozen Axe +10", "max_price": 5000000000, "item_ids": ["9a924d08"]},
    {"name": "Giant Dragon Wing Bow +1", "max_price": 220000000, "item_ids": ["d207a231"]},
    {"name": "Giant Dragon Wing Bow +2", "max_price": 220000000, "item_ids": ["d307a231"]},
    {"name": "Giant Dragon Wing Bow +3", "max_price": 300000000, "item_ids": ["d407a231"]},
    {"name": "Giant Dragon Wing Bow +4", "max_price": 400000000, "item_ids": ["d507a231"]},
    {"name": "Giant Dragon Wing Bow +5", "max_price": 500000000, "item_ids": ["d607a231"]},
    {"name": "Giant Dragon Wing Bow +6", "max_price": 600000000, "item_ids": ["d707a231"]},
    {"name": "Giant Dragon Wing Bow +7", "max_price": 10000000000, "item_ids": ["d807a231"]},
    {"name": "Giant Dragon Wing Bow +8", "max_price": 5000000000, "item_ids": ["d907a231"]},
    {"name": "Giant Dragon Wing Bow +9", "max_price": 5000000000, "item_ids": ["da07a231"]},
    {"name": "Giant Dragon Wing Bow +10", "max_price": 5000000000, "item_ids": ["db07a231"]},
    {"name": "Giant Wrath Spear +1", "max_price": 250000000, "item_ids": ["2b81a031"]},
    {"name": "Giant Wrath Spear +2", "max_price": 250000000, "item_ids": ["2c81a031"]},
    {"name": "Giant Wrath Spear +3", "max_price": 250000000, "item_ids": ["2d81a031"]},
    {"name": "Giant Wrath Spear +4", "max_price": 250000000, "item_ids": ["2e81a031"]},
    {"name": "Giant Wrath Spear +5", "max_price": 250000000, "item_ids": ["2f81a031"]},
    {"name": "Giant Wrath Spear +6", "max_price": 250000000, "item_ids": ["3081a031"]},
    {"name": "Giant Wrath Spear +7", "max_price": 1000000000, "item_ids": ["3181a031"]},
    {"name": "Giant Wrath Spear +8", "max_price": 1000000000, "item_ids": ["3281a031"]},
    {"name": "Giant Wrath Spear +9", "max_price": 5000000000, "item_ids": ["3381a031"]},
    {"name": "Giant Wrath Spear +10", "max_price": 5000000000, "item_ids": ["3481a031"]},
    {"name": "Shade Dagger +5", "max_price": 5000000, "item_ids": ["15eea006", "3deea006"]},
    {"name": "Shade Dagger +6", "max_price": 14000000, "item_ids": ["16eea006", "3eeea006"]},
    {"name": "Shade Dagger +7", "max_price": 20000000, "item_ids": ["17eea006", "3feea006"]},
    {"name": "Shade Dagger +8", "max_price": 220000000, "item_ids": ["40eea006", "18eea006"]},
    {"name": "Shade Dagger +9", "max_price": 5000000000, "item_ids": ["41eea006", "19eea006"]},
    {"name": "Shade Dagger +10", "max_price": 5000000000, "item_ids": ["42eea006", "1aeea006"]},
    {"name": "Shade Dagger Reb+1", "max_price": 20000000, "item_ids": ["17f2a006"]},
    {"name": "Shade Dagger Reb+2", "max_price": 80000000, "item_ids": ["18f2a006"]},
    {"name": "Shade Dagger Reb+3", "max_price": 30000000, "item_ids": ["19f2a006"]},
    {"name": "Shade Dagger Reb+4", "max_price": 220000000, "item_ids": ["1af2a006"]},
    {"name": "Shade Dagger Reb+5", "max_price": 220000000, "item_ids": ["1bf2a006"]},
    {"name": "Shade Dagger Reb+6", "max_price": 300000000, "item_ids": ["1cf2a006"]},
    {"name": "Shade Dagger Reb+7", "max_price": 400000000, "item_ids": ["1df2a006"]},
    {"name": "Shade Dagger Reb+8", "max_price": 500000000, "item_ids": ["1ef2a006"]},
    {"name": "Shade Dagger Reb+9", "max_price": 1000000000, "item_ids": ["1ff2a006"]},
    {"name": "Shade Dagger Reb+10", "max_price": 5000000000, "item_ids": ["20f2a006"]},
    {"name": "Shade Dagger Reb+11", "max_price": 5000000000, "item_ids": ["21f2a006"]},
    {"name": "Shade Dagger Reb+12", "max_price": 5000000000, "item_ids": ["22f2a006"]},
    {"name": "Shade Dagger Reb+13", "max_price": 5000000000, "item_ids": ["23f2a006"]},
    {"name": "Shade Dagger Reb+14", "max_price": 5000000000, "item_ids": ["24f2a006"]},
    {"name": "Shade Dagger Reb+15", "max_price": 5000000000, "item_ids": ["25f2a006"]},
    {"name": "Shade Dagger Reb+16", "max_price": 5000000000, "item_ids": ["26f2a006"]},
    {"name": "Shade Dagger Reb+17", "max_price": 5000000000, "item_ids": ["27f2a006"]},
    {"name": "Shade Dagger Reb+18", "max_price": 5000000000, "item_ids": ["28f2a006"]},
    {"name": "Shade Dagger Reb+19", "max_price": 5000000000, "item_ids": ["29f2a006"]},
    {"name": "Shade Dagger Reb+20", "max_price": 5000000000, "item_ids": ["2af2a006"]},
    {"name": "Shade Dagger Reb+21", "max_price": 5000000000, "item_ids": ["2bf2a006"]},
    {"name": "Reaper +5", "max_price": 5000000, "item_ids": ["55934f09", "7d934f09"]},
    {"name": "Reaper +6", "max_price": 15000000, "item_ids": ["56934f09", "7e934f09"]},
    {"name": "Reaper +7", "max_price": 30000000, "item_ids": ["7f934f09", "57934f09"]},
    {"name": "Reaper +8", "max_price": 220000000, "item_ids": ["58934f09", "80934f09"]},
    {"name": "Reaper +9", "max_price": 5000000000, "item_ids": ["81934f09", "59934f09"]},
    {"name": "Reaper +10", "max_price": 5000000000, "item_ids": ["82934f09", "5a934f09"]},
    {"name": "Reaper Reb+1", "max_price": 30000000, "item_ids": ["57974f09"]},
    {"name": "Reaper Reb+2", "max_price": 30000000, "item_ids": ["58974f09"]},
    {"name": "Reaper Reb+3", "max_price": 80000000, "item_ids": ["59974f09"]},
    {"name": "Reaper Reb+4", "max_price": 220000000, "item_ids": ["5a974f09"]},
    {"name": "Reaper Reb+5", "max_price": 220000000, "item_ids": ["5b974f09"]},
    {"name": "Reaper Reb+6", "max_price": 500000000, "item_ids": ["5c974f09"]},
    {"name": "Reaper Reb+7", "max_price": 500000000, "item_ids": ["5d974f09"]},
    {"name": "Reaper Reb+8", "max_price": 600000000, "item_ids": ["5e974f09"]},
    {"name": "Reaper Reb+9", "max_price": 900000000, "item_ids": ["5f974f09"]},
    {"name": "Reaper Reb+10", "max_price": 5000000000, "item_ids": ["60974f09"]},
    {"name": "Reaper Reb+11", "max_price": 5000000000, "item_ids": ["61974f09"]},
    {"name": "Reaper Reb+12", "max_price": 5000000000, "item_ids": ["62974f09"]},
    {"name": "Reaper Reb+13", "max_price": 5000000000, "item_ids": ["63974f09"]},
    {"name": "Reaper Reb+14", "max_price": 5000000000, "item_ids": ["64974f09"]},
    {"name": "Reaper Reb+15", "max_price": 5000000000, "item_ids": ["65974f09"]},
    {"name": "Reaper Reb+16", "max_price": 5000000000, "item_ids": ["66974f09"]},
    {"name": "Reaper Reb+17", "max_price": 5000000000, "item_ids": ["67974f09"]},
    {"name": "Reaper Reb+18", "max_price": 5000000000, "item_ids": ["68974f09"]},
    {"name": "Reaper Reb+19", "max_price": 5000000000, "item_ids": ["69974f09"]},
    {"name": "Reaper Reb+20", "max_price": 5000000000, "item_ids": ["6a974f09"]},
    {"name": "Reaper Reb+21", "max_price": 5000000000, "item_ids": ["6b974f09"]},
    {"name": "Thunder Impact +5", "max_price": 6000000, "item_ids": ["d5fcb608", "fdfdb608"]},
    {"name": "Thunder Impact +6", "max_price": 15000000, "item_ids": ["d6fcb608", "fefdb608"]},
    {"name": "Thunder Impact +7", "max_price": 30000000, "item_ids": ["d7fcb608", "fffdb608"]},
    {"name": "Thunder Impact +8", "max_price": 220000000, "item_ids": ["00fdb608", "d8fcb608"]},
    {"name": "Thunder Impact +9", "max_price": 5000000000, "item_ids": ["01fdb608", "d9fcb608"]},
    {"name": "Thunder Impact +10", "max_price": 5000000000, "item_ids": ["02fdb608", "dafcb608"]},
    {"name": "Thunder Impact Reb+1", "max_price": 30000000, "item_ids": ["d700b708"]},
    {"name": "Thunder Impact Reb+2", "max_price": 40000000, "item_ids": ["d800b708"]},
    {"name": "Thunder Impact Reb+3", "max_price": 50000000, "item_ids": ["d900b708"]},
    {"name": "Thunder Impact Reb+4", "max_price": 220000000, "item_ids": ["da00b708"]},
    {"name": "Thunder Impact Reb+5", "max_price": 220000000, "item_ids": ["db00b708"]},
    {"name": "Thunder Impact Reb+6", "max_price": 250000000, "item_ids": ["dc00b708"]},
    {"name": "Thunder Impact Reb+7", "max_price": 400000000, "item_ids": ["dd00b708"]},
    {"name": "Thunder Impact Reb+8", "max_price": 600000000, "item_ids": ["de00b708"]},
    {"name": "Thunder Impact Reb+9", "max_price": 1000000000, "item_ids": ["df00b708"]},
    {"name": "Thunder Impact Reb+10", "max_price": 4000000000, "item_ids": ["e000b708"]},
    {"name": "Thunder Impact Reb+11", "max_price": 5000000000, "item_ids": ["e100b708"]},
    {"name": "Thunder Impact Reb+12", "max_price": 5000000000, "item_ids": ["e200b708"]},
    {"name": "Thunder Impact Reb+13", "max_price": 5000000000, "item_ids": ["e300b708"]},
    {"name": "Thunder Impact Reb+14", "max_price": 5000000000, "item_ids": ["e400b708"]},
    {"name": "Thunder Impact Reb+15", "max_price": 5000000000, "item_ids": ["e500b708"]},
    {"name": "Thunder Impact Reb+16", "max_price": 5000000000, "item_ids": ["e600b708"]},
    {"name": "Thunder Impact Reb+17", "max_price": 5000000000, "item_ids": ["e700b708"]},
    {"name": "Thunder Impact Reb+18", "max_price": 5000000000, "item_ids": ["e800b708"]},
    {"name": "Thunder Impact Reb+19", "max_price": 5000000000, "item_ids": ["e900b708"]},
    {"name": "Thunder Impact Reb+20", "max_price": 5000000000, "item_ids": ["ea00b708"]},
    {"name": "Thunder Impact Reb+21", "max_price": 5000000000, "item_ids": ["eb00b708"]},
    {"name": "IronShade Bow +5", "max_price": 5000000, "item_ids": ["95bb090a", "bdbb090a"]},
    {"name": "IronShade Bow +6", "max_price": 15000000, "item_ids": ["96bb090a", "bebb090a"]},
    {"name": "IronShade Bow +7", "max_price": 30000000, "item_ids": ["bfbb090a", "97bb090a"]},
    {"name": "IronShade Bow +8", "max_price": 220000000, "item_ids": ["98bb090a", "c0bb090a"]},
    {"name": "IronShade Bow +9", "max_price": 5000000000, "item_ids": ["99bb090a", "c1bb090a"]},
    {"name": "IronShade Bow +10", "max_price": 5000000000, "item_ids": ["9abb090a", "c2bb090a"]},
    {"name": "IronShade Bow Reb+1", "max_price": 30000000, "item_ids": ["97bf090a"]},
    {"name": "IronShade Bow Reb+2", "max_price": 40000000, "item_ids": ["98bf090a"]},
    {"name": "IronShade Bow Reb+3", "max_price": 60000000, "item_ids": ["99bf090a"]},
    {"name": "IronShade Bow Reb+4", "max_price": 220000000, "item_ids": ["9abf090a"]},
    {"name": "IronShade Bow Reb+5", "max_price": 220000000, "item_ids": ["9bbf090a"]},
    {"name": "IronShade Bow Reb+6", "max_price": 300000000, "item_ids": ["9cbf090a"]},
    {"name": "IronShade Bow Reb+7", "max_price": 400000000, "item_ids": ["9dbf090a"]},
    {"name": "IronShade Bow Reb+8", "max_price": 700000000, "item_ids": ["9ebf090a"]},
    {"name": "IronShade Bow Reb+9", "max_price": 1000000000, "item_ids": ["9fbf090a"]},
    {"name": "IronShade Bow Reb+10", "max_price": 4500000000, "item_ids": ["a0bf090a"]},
    {"name": "IronShade Bow Reb+11", "max_price": 5000000000, "item_ids": ["a1bf090a"]},
    {"name": "IronShade Bow Reb+12", "max_price": 5000000000, "item_ids": ["a2bf090a"]},
    {"name": "IronShade Bow Reb+13", "max_price": 5000000000, "item_ids": ["a3bf090a"]},
    {"name": "IronShade Bow Reb+14", "max_price": 5000000000, "item_ids": ["a4bf090a"]},
    {"name": "IronShade Bow Reb+15", "max_price": 5000000000, "item_ids": ["a5bf090a"]},
    {"name": "IronShade Bow Reb+16", "max_price": 5000000000, "item_ids": ["a6bf090a"]},
    {"name": "IronShade Bow Reb+17", "max_price": 5000000000, "item_ids": ["a7bf090a"]},
    {"name": "IronShade Bow Reb+18", "max_price": 5000000000, "item_ids": ["a8bf090a"]},
    {"name": "IronShade Bow Reb+19", "max_price": 5000000000, "item_ids": ["a9bf090a"]},
    {"name": "IronShade Bow Reb+20", "max_price": 5000000000, "item_ids": ["aabf090a"]},
    {"name": "IronShade Bow Reb+21", "max_price": 5000000000, "item_ids": ["abbf090a"]},
    {"name": "Bloody Dagger +7", "max_price": 5000000, "item_ids": ["9f679f06", "77679f06"]},
    {"name": "Bloody Dagger +8", "max_price": 220000000, "item_ids": ["a0679f06", "78679f06"]},
    {"name": "Bloody Dagger +9", "max_price": 500000000, "item_ids": ["a1679f06", "79679f06"]},
    {"name": "Bloody Dagger +10", "max_price": 5000000000, "item_ids": ["a2679f06", "7a679f06"]},
    {"name": "Bloody Dagger Reb+1", "max_price": 5000000, "item_ids": ["776b9f06"]},
    {"name": "Bloody Dagger Reb+2", "max_price": 20000000, "item_ids": ["786b9f06"]},
    {"name": "Bloody Dagger Reb+3", "max_price": 30000000, "item_ids": ["796b9f06"]},
    {"name": "Bloody Dagger Reb+4", "max_price": 35000000, "item_ids": ["7a6b9f06"]},
    {"name": "Bloody Dagger Reb+5", "max_price": 220000000, "item_ids": ["7b6b9f06"]},
    {"name": "Bloody Dagger Reb+6", "max_price": 250000000, "item_ids": ["7c6b9f06"]},
    {"name": "Bloody Dagger Reb+7", "max_price": 250000000, "item_ids": ["7d6b9f06"]},
    {"name": "Bloody Dagger Reb+8", "max_price": 300000000, "item_ids": ["7e6b9f06"]},
    {"name": "Bloody Dagger Reb+9", "max_price": 400000000, "item_ids": ["7f6b9f06"]},
    {"name": "Bloody Dagger Reb+10", "max_price": 500000000, "item_ids": ["806b9f06"]},
    {"name": "Bloody Dagger Reb+11", "max_price": 700000000, "item_ids": ["816b9f06"]},
    {"name": "Bloody Dagger Reb+12", "max_price": 1000000000, "item_ids": ["826b9f06"]},
    {"name": "Bloody Dagger Reb+13", "max_price": 2000000000, "item_ids": ["836b9f06"]},
    {"name": "Bloody Dagger Reb+14", "max_price": 5000000000, "item_ids": ["846b9f06"]},
    {"name": "Bloody Dagger Reb+15", "max_price": 5000000000, "item_ids": ["856b9f06"]},
    {"name": "Bloody Dagger Reb+16", "max_price": 5000000000, "item_ids": ["866b9f06"]},
    {"name": "Bloody Dagger Reb+17", "max_price": 5000000000, "item_ids": ["876b9f06"]},
    {"name": "Bloody Dagger Reb+18", "max_price": 5000000000, "item_ids": ["886b9f06"]},
    {"name": "Bloody Dagger Reb+19", "max_price": 5000000000, "item_ids": ["896b9f06"]},
    {"name": "Bloody Dagger Reb+20", "max_price": 5000000000, "item_ids": ["8a6b9f06"]},
    {"name": "Bloody Dagger Reb+21", "max_price": 5000000000, "item_ids": ["8b6b9f06"]},
    {"name": "Phantom Sword +5", "max_price": 3000000, "item_ids": ["15dd8807", "3ddd8807"]},
    {"name": "Phantom Sword +6", "max_price": 12000000, "item_ids": ["16dd8807", "3edd8807"]},
    {"name": "Phantom Sword +7", "max_price": 50000000, "item_ids": ["3fdd8807", "17dd8807"]},
    {"name": "Phantom Sword +8", "max_price": 220000000, "item_ids": ["18dd8807", "40dd8807"]},
    {"name": "Phantom Sword +9", "max_price": 5000000000, "item_ids": ["41dd8807", "19dd8807"]},
    {"name": "Phantom Sword +10", "max_price": 5000000000, "item_ids": ["42dd8807", "1add8807"]},
    {"name": "Phantom Sword Reb+1", "max_price": 50000000, "item_ids": ["17e18807"]},
    {"name": "Phantom Sword Reb+2", "max_price": 60000000, "item_ids": ["18e18807"]},
    {"name": "Phantom Sword Reb+3", "max_price": 80000000, "item_ids": ["19e18807"]},
    {"name": "Phantom Sword Reb+4", "max_price": 220000000, "item_ids": ["1ae18807"]},
    {"name": "Phantom Sword Reb+5", "max_price": 220000000, "item_ids": ["1be18807"]},
    {"name": "Phantom Sword Reb+6", "max_price": 300000000, "item_ids": ["1ce18807"]},
    {"name": "Phantom Sword Reb+7", "max_price": 500000000, "item_ids": ["1de18807"]},
    {"name": "Phantom Sword Reb+8", "max_price": 800000000, "item_ids": ["1ee18807"]},
    {"name": "Phantom Sword Reb+9", "max_price": 1250000000, "item_ids": ["1fe18807"]},
    {"name": "Phantom Sword Reb+10", "max_price": 2500000000, "item_ids": ["20e18807"]},
    {"name": "Phantom Sword Reb+11", "max_price": 4000000000, "item_ids": ["21e18807"]},
    {"name": "Phantom Sword Reb+12", "max_price": 5000000000, "item_ids": ["22e18807"]},
    {"name": "Phantom Sword Reb+13", "max_price": 5000000000, "item_ids": ["23e18807"]},
    {"name": "Phantom Sword Reb+14", "max_price": 5000000000, "item_ids": ["24e18807"]},
    {"name": "Phantom Sword Reb+15", "max_price": 5000000000, "item_ids": ["25e18807"]},
    {"name": "Phantom Sword Reb+16", "max_price": 5000000000, "item_ids": ["26e18807"]},
    {"name": "Phantom Sword Reb+17", "max_price": 5000000000, "item_ids": ["27e18807"]},
    {"name": "Phantom Sword Reb+18", "max_price": 5000000000, "item_ids": ["28e18807"]},
    {"name": "Phantom Sword Reb+19", "max_price": 5000000000, "item_ids": ["29e18807"]},
    {"name": "Phantom Sword Reb+20", "max_price": 5000000000, "item_ids": ["2ae18807"]},
    {"name": "Phantom Sword Reb+21", "max_price": 5000000000, "item_ids": ["2be18807"]},
    {"name": "Giant Reaper +5", "max_price": 10000000, "item_ids": ["1d1a5109", "f5195109"]},
    {"name": "Giant Reaper +6", "max_price": 18000000, "item_ids": ["f6195109", "1e1a5109"]},
    {"name": "Giant Reaper +7", "max_price": 50000000, "item_ids": ["1f1a5109", "f7195109"]},
    {"name": "Giant Reaper +8", "max_price": 220000000, "item_ids": ["201a5109", "f8195109"]},
    {"name": "Giant Reaper +9", "max_price": 5000000000, "item_ids": ["211a5109", "f9195109"]},
    {"name": "Giant Reaper +10", "max_price": 5000000000, "item_ids": ["221a5109", "fa195109"]},
    {"name": "Giant Reaper Reb+1", "max_price": 50000000, "item_ids": ["f71d5109"]},
    {"name": "Giant Reaper Reb+2", "max_price": 100000000, "item_ids": ["f81d5109"]},
    {"name": "Giant Reaper Reb+3", "max_price": 220000000, "item_ids": ["f91d5109"]},
    {"name": "Giant Reaper Reb+4", "max_price": 220000000, "item_ids": ["fa1d5109"]},
    {"name": "Giant Reaper Reb+5", "max_price": 220000000, "item_ids": ["fb1d5109"]},
    {"name": "Giant Reaper Reb+6", "max_price": 400000000, "item_ids": ["fc1d5109"]},
    {"name": "Giant Reaper Reb+7", "max_price": 800000000, "item_ids": ["fd1d5109"]},
    {"name": "Giant Reaper Reb+8", "max_price": 1600000000, "item_ids": ["fe1d5109"]},
    {"name": "Giant Reaper Reb+9", "max_price": 3200000000, "item_ids": ["ff1d5109"]},
    {"name": "Giant Reaper Reb+10", "max_price": 5000000000, "item_ids": ["001d5109"]},
    {"name": "Giant Reaper Reb+11", "max_price": 5000000000, "item_ids": ["011d5109"]},
    {"name": "Giant Reaper Reb+12", "max_price": 5000000000, "item_ids": ["021d5109"]},
    {"name": "Giant Reaper Reb+13", "max_price": 5000000000, "item_ids": ["031d5109"]},
    {"name": "Giant Reaper Reb+14", "max_price": 5000000000, "item_ids": ["041d5109"]},
    {"name": "Giant Reaper Reb+15", "max_price": 5000000000, "item_ids": ["051d5109"]},
    {"name": "Giant Reaper Reb+16", "max_price": 5000000000, "item_ids": ["061d5109"]},
    {"name": "Giant Reaper Reb+17", "max_price": 5000000000, "item_ids": ["071d5109"]},
    {"name": "Giant Reaper Reb+18", "max_price": 5000000000, "item_ids": ["081d5109"]},
    {"name": "Giant Reaper Reb+19", "max_price": 5000000000, "item_ids": ["091d5109"]},
    {"name": "Giant Reaper Reb+20", "max_price": 5000000000, "item_ids": ["0a1d5109"]},
    {"name": "Giant Reaper Reb+21", "max_price": 5000000000, "item_ids": ["0b1d5109"]},
    {"name": "Giant Thunder Impact +5", "max_price": 5000000, "item_ids": ["9d83b808", "7583b808"]},
    {"name": "Giant Thunder Impact +6", "max_price": 10000000, "item_ids": ["9e83b808", "7683b808"]},
    {"name": "Giant Thunder Impact +7", "max_price": 50000000, "item_ids": ["9f83b808", "7783b808"]},
    {"name": "Giant Thunder Impact +8", "max_price": 220000000, "item_ids": ["a083b808", "7883b808"]},
    {"name": "Giant Thunder Impact +9", "max_price": 5000000000, "item_ids": ["a183b808", "7983b808"]},
    {"name": "Giant Thunder Impact +10", "max_price": 5000000000, "item_ids": ["a283b808", "7a83b808"]},
    {"name": "Giant Thunder Impact Reb+1", "max_price": 50000000, "item_ids": ["7787b808"]},
    {"name": "Giant Thunder Impact Reb+2", "max_price": 60000000, "item_ids": ["7887b808"]},
    {"name": "Giant Thunder Impact Reb+3", "max_price": 90000000, "item_ids": ["7987b808"]},
    {"name": "Giant Thunder Impact Reb+4", "max_price": 220000000, "item_ids": ["7a87b808"]},
    {"name": "Giant Thunder Impact Reb+5", "max_price": 220000000, "item_ids": ["7b87b808"]},
    {"name": "Giant Thunder Impact Reb+6", "max_price": 300000000, "item_ids": ["7c87b808"]},
    {"name": "Giant Thunder Impact Reb+7", "max_price": 600000000, "item_ids": ["7d87b808"]},
    {"name": "Giant Thunder Impact Reb+8", "max_price": 1200000000, "item_ids": ["7e87b808"]},
    {"name": "Giant Thunder Impact Reb+9", "max_price": 2400000000, "item_ids": ["7f87b808"]},
    {"name": "Giant Thunder Impact Reb+10", "max_price": 3600000000, "item_ids": ["8087b808"]},
    {"name": "Giant Thunder Impact Reb+11", "max_price": 5000000000, "item_ids": ["8187b808"]},
    {"name": "Giant Thunder Impact Reb+12", "max_price": 5000000000, "item_ids": ["8287b808"]},
    {"name": "Giant Thunder Impact Reb+13", "max_price": 5000000000, "item_ids": ["8387b808"]},
    {"name": "Giant Thunder Impact Reb+14", "max_price": 5000000000, "item_ids": ["8487b808"]},
    {"name": "Giant Thunder Impact Reb+15", "max_price": 5000000000, "item_ids": ["8587b808"]},
    {"name": "Giant Thunder Impact Reb+16", "max_price": 5000000000, "item_ids": ["8687b808"]},
    {"name": "Giant Thunder Impact Reb+17", "max_price": 5000000000, "item_ids": ["8787b808"]},
    {"name": "Giant Thunder Impact Reb+18", "max_price": 5000000000, "item_ids": ["8887b808"]},
    {"name": "Giant Thunder Impact Reb+19", "max_price": 5000000000, "item_ids": ["8987b808"]},
    {"name": "Giant Thunder Impact Reb+20", "max_price": 5000000000, "item_ids": ["8a87b808"]},
    {"name": "Giant Thunder Impact Reb+21", "max_price": 5000000000, "item_ids": ["8b87b808"]},
    {"name": "Giant Phantom Sword +5", "max_price": 5000000, "item_ids": ["7dea8b07"]},
    {"name": "Giant Phantom Sword +6", "max_price": 15000000, "item_ids": ["7eea8b07"]},
    {"name": "Giant Phantom Sword +7", "max_price": 50000000, "item_ids": ["7fea8b07"]},
    {"name": "Giant Phantom Sword +8", "max_price": 220000000, "item_ids": ["80ea8b07"]},
    {"name": "Giant Phantom Sword +9", "max_price": 5000000000, "item_ids": ["81ea8b07"]},
    {"name": "Giant Phantom Sword +10", "max_price": 5000000000, "item_ids": ["82ea8b07"]},
    {"name": "Giant Phantom Sword Reb+1", "max_price": 50000000, "item_ids": ["57ee8b07"]},
    {"name": "Giant Phantom Sword Reb+2", "max_price": 60000000, "item_ids": ["58ee8b07"]},
    {"name": "Giant Phantom Sword Reb+3", "max_price": 80000000, "item_ids": ["59ee8b07"]},
    {"name": "Giant Phantom Sword Reb+4", "max_price": 220000000, "item_ids": ["5aee8b07"]},
    {"name": "Giant Phantom Sword Reb+5", "max_price": 220000000, "item_ids": ["5bee8b07"]},
    {"name": "Giant Phantom Sword Reb+6", "max_price": 2500000000, "item_ids": ["5cee8b07"]},
    {"name": "Giant Phantom Sword Reb+7", "max_price": 500000000, "item_ids": ["5dee8b07"]},
    {"name": "Giant Phantom Sword Reb+8", "max_price": 1000000000, "item_ids": ["5eee8b07"]},
    {"name": "Giant Phantom Sword Reb+9", "max_price": 2000000000, "item_ids": ["5fee8b07"]},
    {"name": "Giant Phantom Sword Reb+10", "max_price": 3500000000, "item_ids": ["60ee8b07"]},
    {"name": "Giant Phantom Sword Reb+11", "max_price": 5000000000, "item_ids": ["61ee8b07"]},
    {"name": "Giant Phantom Sword Reb+12", "max_price": 5000000000, "item_ids": ["62ee8b07"]},
    {"name": "Giant Phantom Sword Reb+13", "max_price": 5000000000, "item_ids": ["63ee8b07"]},
    {"name": "Giant Phantom Sword Reb+14", "max_price": 5000000000, "item_ids": ["64ee8b07"]},
    {"name": "Giant Phantom Sword Reb+15", "max_price": 5000000000, "item_ids": ["65ee8b07"]},
    {"name": "Giant Phantom Sword Reb+16", "max_price": 5000000000, "item_ids": ["66ee8b07"]},
    {"name": "Giant Phantom Sword Reb+17", "max_price": 5000000000, "item_ids": ["67ee8b07"]},
    {"name": "Giant Phantom Sword Reb+18", "max_price": 5000000000, "item_ids": ["68ee8b07"]},
    {"name": "Giant Phantom Sword Reb+19", "max_price": 5000000000, "item_ids": ["69ee8b07"]},
    {"name": "Giant Phantom Sword Reb+20", "max_price": 5000000000, "item_ids": ["6aee8b07"]},
    {"name": "Giant Phantom Sword Reb+21", "max_price": 5000000000, "item_ids": ["6bee8b07"]},
    {"name": "Giant IronShade Bow +7", "max_price": 50000000, "item_ids": ["ffc80c0a", "d7c80c0a", "ffc90c0a"]},
    {"name": "Giant IronShade Bow +8", "max_price": 220000000, "item_ids": ["00c90c0a", "d8c80c0a", "00c80c0a"]},
    {"name": "Giant IronShade Bow +9", "max_price": 5000000000, "item_ids": ["01c80c0a", "d9c80c0a", "01c90c0a"]},
    {"name": "Giant IronShade Bow +10", "max_price": 5000000000, "item_ids": ["02c80c0a", "dac80c0a", "02c90c0a"]},
    {"name": "Giant IronShade Bow Reb+1", "max_price": 50000000, "item_ids": ["d7cc0c0a"]},
    {"name": "Giant IronShade Bow Reb+2", "max_price": 60000000, "item_ids": ["d8cc0c0a"]},
    {"name": "Giant IronShade Bow Reb+3", "max_price": 70000000, "item_ids": ["d9cc0c0a"]},
    {"name": "Giant IronShade Bow Reb+4", "max_price": 220000000, "item_ids": ["dacc0c0a"]},
    {"name": "Giant IronShade Bow Reb+5", "max_price": 220000000, "item_ids": ["dbcc0c0a"]},
    {"name": "Giant IronShade Bow Reb+6", "max_price": 300000000, "item_ids": ["dccc0c0a"]},
    {"name": "Giant IronShade Bow Reb+7", "max_price": 600000000, "item_ids": ["ddcc0c0a"]},
    {"name": "Giant IronShade Bow Reb+8", "max_price": 1200000000, "item_ids": ["decc0c0a"]},
    {"name": "Giant IronShade Bow Reb+9", "max_price": 2400000000, "item_ids": ["dfcc0c0a"]},
    {"name": "Giant IronShade Bow Reb+10", "max_price": 3600000000, "item_ids": ["e0cc0c0a"]},
    {"name": "Giant IronShade Bow Reb+11", "max_price": 5000000000, "item_ids": ["e1cc0c0a"]},
    {"name": "Giant IronShade Bow Reb+12", "max_price": 5000000000, "item_ids": ["e2cc0c0a"]},
    {"name": "Giant IronShade Bow Reb+13", "max_price": 5000000000, "item_ids": ["e3cc0c0a"]},
    {"name": "Giant IronShade Bow Reb+14", "max_price": 5000000000, "item_ids": ["e4cc0c0a"]},
    {"name": "Giant IronShade Bow Reb+15", "max_price": 5000000000, "item_ids": ["e5cc0c0a"]},
    {"name": "Giant IronShade Bow Reb+16", "max_price": 5000000000, "item_ids": ["e6cc0c0a"]},
    {"name": "Giant IronShade Bow Reb+17", "max_price": 5000000000, "item_ids": ["e7cc0c0a"]},
    {"name": "Giant IronShade Bow Reb+18", "max_price": 5000000000, "item_ids": ["e8cc0c0a"]},
    {"name": "Giant IronShade Bow Reb+19", "max_price": 5000000000, "item_ids": ["e9cc0c0a"]},
    {"name": "Giant IronShade Bow Reb+20", "max_price": 5000000000, "item_ids": ["eacc0c0a"]},
    {"name": "Giant IronShade Bow Reb+21", "max_price": 5000000000, "item_ids": ["ebcc0c0a"]},
    {"name": "Giant Shade Dagger +5", "max_price": 5000000, "item_ids": ["dd74a206", "b574a206"]},
    {"name": "Giant Shade Dagger +6", "max_price": 15000000, "item_ids": ["de74a206", "b674a206"]},
    {"name": "Giant Shade Dagger +7", "max_price": 100000000, "item_ids": ["df74a206", "b774a206"]},
    {"name": "Giant Shade Dagger +8", "max_price": 220000000, "item_ids": ["e074a206", "b874a206"]},
    {"name": "Giant Shade Dagger +9", "max_price": 5000000000, "item_ids": ["e174a206", "b974a206"]},
    {"name": "Giant Shade Dagger +10", "max_price": 5000000000, "item_ids": ["e274a206", "ba74a206"]},
    {"name": "Giant Shade Dagger Reb+1", "max_price": 100000000, "item_ids": ["b778a206"]},
    {"name": "Giant Shade Dagger Reb+2", "max_price": 100000000, "item_ids": ["b878a206"]},
    {"name": "Giant Shade Dagger Reb+3", "max_price": 220000000, "item_ids": ["b978a206"]},
    {"name": "Giant Shade Dagger Reb+4", "max_price": 220000000, "item_ids": ["ba78a206"]},
    {"name": "Giant Shade Dagger Reb+5", "max_price": 220000000, "item_ids": ["bb78a206"]},
    {"name": "Giant Shade Dagger Reb+6", "max_price": 300000000, "item_ids": ["bc78a206"]},
    {"name": "Giant Shade Dagger Reb+7", "max_price": 500000000, "item_ids": ["bd78a206"]},
    {"name": "Giant Shade Dagger Reb+8", "max_price": 600000000, "item_ids": ["be78a206"]},
    {"name": "Giant Shade Dagger Reb+9", "max_price": 1000000000, "item_ids": ["bf78a206"]},
    {"name": "Giant Shade Dagger Reb+10", "max_price": 5000000000, "item_ids": ["c078a206"]},
    {"name": "Giant Shade Dagger Reb+11", "max_price": 5000000000, "item_ids": ["c178a206"]},
    {"name": "Giant Shade Dagger Reb+12", "max_price": 5000000000, "item_ids": ["c278a206"]},
    {"name": "Giant Shade Dagger Reb+13", "max_price": 5000000000, "item_ids": ["c378a206"]},
    {"name": "Giant Shade Dagger Reb+14", "max_price": 5000000000, "item_ids": ["c478a206"]},
    {"name": "Giant Shade Dagger Reb+15", "max_price": 5000000000, "item_ids": ["c578a206"]},
    {"name": "Giant Shade Dagger Reb+16", "max_price": 5000000000, "item_ids": ["c678a206"]},
    {"name": "Giant Shade Dagger Reb+17", "max_price": 5000000000, "item_ids": ["c778a206"]},
    {"name": "Giant Shade Dagger Reb+18", "max_price": 5000000000, "item_ids": ["c878a206"]},
    {"name": "Giant Shade Dagger Reb+19", "max_price": 5000000000, "item_ids": ["c978a206"]},
    {"name": "Giant Shade Dagger Reb+20", "max_price": 5000000000, "item_ids": ["ca78a206"]},
    {"name": "Giant Shade Dagger Reb+21", "max_price": 5000000000, "item_ids": ["cb78a206"]},
    {"name": "Bloody Bow +7", "max_price": 10000000, "item_ids": ["1f35080a", "f734080a"]},
    {"name": "Bloody Bow +8", "max_price": 220000000, "item_ids": ["2035080a", "f834080a"]},
    {"name": "Bloody Bow +9", "max_price": 3000000000, "item_ids": ["2135080a", "f934080a"]},
    {"name": "Bloody Bow +10", "max_price": 5000000000, "item_ids": ["2235080a", "fa34080a"]},
    {"name": "Bloody Bow Reb+1", "max_price": 10000000, "item_ids": ["f738080a"]},
    {"name": "Bloody Bow Reb+2", "max_price": 15000000, "item_ids": ["f838080a"]},
    {"name": "Bloody Bow Reb+3", "max_price": 35000000, "item_ids": ["f938080a"]},
    {"name": "Bloody Bow Reb+4", "max_price": 45000000, "item_ids": ["fa38080a"]},
    {"name": "Bloody Bow Reb+5", "max_price": 70000000, "item_ids": ["fb38080a"]},
    {"name": "Bloody Bow Reb+6", "max_price": 150000000, "item_ids": ["fc38080a"]},
    {"name": "Bloody Bow Reb+7", "max_price": 250000000, "item_ids": ["fd38080a"]},
    {"name": "Bloody Bow Reb+8", "max_price": 350000000, "item_ids": ["fe38080a"]},
    {"name": "Bloody Bow Reb+9", "max_price": 500000000, "item_ids": ["ff38080a"]},
    {"name": "Bloody Bow Reb+10", "max_price": 700000000, "item_ids": ["0038080a"]},
    {"name": "Bloody Bow Reb+11", "max_price": 1000000000, "item_ids": ["0138080a"]},
    {"name": "Bloody Bow Reb+12", "max_price": 1200000000, "item_ids": ["0238080a"]},
    {"name": "Bloody Bow Reb+13", "max_price": 2500000000, "item_ids": ["0338080a"]},
    {"name": "Bloody Bow Reb+14", "max_price": 5000000000, "item_ids": ["0438080a"]},
    {"name": "Bloody Bow Reb+15", "max_price": 5000000000, "item_ids": ["0538080a"]},
    {"name": "Bloody Bow Reb+16", "max_price": 5000000000, "item_ids": ["0638080a"]},
    {"name": "Bloody Bow Reb+17", "max_price": 5000000000, "item_ids": ["0738080a"]},
    {"name": "Bloody Bow Reb+18", "max_price": 5000000000, "item_ids": ["0838080a"]},
    {"name": "Bloody Bow Reb+19", "max_price": 5000000000, "item_ids": ["0938080a"]},
    {"name": "Bloody Bow Reb+20", "max_price": 5000000000, "item_ids": ["0a38080a"]},
    {"name": "Bloody Bow Reb+21", "max_price": 5000000000, "item_ids": ["0b38080a"]},
    {"name": "Master Warrior Earring Old", "max_price": 1000000, "item_ids": ["956ed117"]},
    {"name": "Master Warrior Earring +0", "max_price": 1000000, "item_ids": []},
    {"name": "Master Warrior Earring +1", "max_price": 250000000, "item_ids": ["1b068212"]},
    {"name": "Master Warrior Earring +3", "max_price": 1000000000, "item_ids": ["1d068212"]},
    {"name": "Master Rogue Earring Old", "max_price": 40000000, "item_ids": ["7e72d117"]},
    {"name": "Master Rogue Earring +0", "max_price": 220000000, "item_ids": ["f8098212"]},
    {"name": "Master Rogue Earring +1", "max_price": 50000000, "item_ids": []},
    {"name": "Master Mage Earring Old", "max_price": 10000000, "item_ids": []},
    {"name": "Master Priest Earring Old", "max_price": 10000000, "item_ids": ["507ad117"]},
    {"name": "Master Priest Earring +0", "max_price": 20000000, "item_ids": []},
    {"name": "Master Courage Ring Old", "max_price": 1000000, "item_ids": ["6d7dd117"]},
    {"name": "Master Courage Ring +0", "max_price": 15000000, "item_ids": ["3019ad13"]},
    {"name": "Master Courage Ring +1", "max_price": 250000000, "item_ids": ["d119ad13"]},
    {"name": "Master Courage Ring +2", "max_price": 1000000000, "item_ids": ["d219ad13"]},
    {"name": "Master Courage Ring +3", "max_price": 1000000000, "item_ids": ["d319ad13"]},
    {"name": "Master Hextech Ring Old", "max_price": 2000000, "item_ids": ["5681d117"]},
    {"name": "Master Hextech Ring +0", "max_price": 2000000, "item_ids": []},
    {"name": "Master Hextech Ring +1", "max_price": 220000000, "item_ids": ["1bb6ad13"]},
    {"name": "Master Hextech Ring +2", "max_price": 220000000, "item_ids": ["1cb6ad13"]},
    {"name": "Master Hextech Ring +3", "max_price": 220000000, "item_ids": ["1db6ad13"]},
    {"name": "Master Belt Of Courage Old", "max_price": 50000000, "item_ids": ["8a89d117"]},
    {"name": "Master Belt Of Str Old", "max_price": 1000000, "item_ids": ["738dd117"]},
    {"name": "Master Belt Of Str +0", "max_price": 1000000, "item_ids": []},
    {"name": "Master Belt Of Dexterity Old", "max_price": 2000000, "item_ids": ["5c91d117"]},
    {"name": "Elarin Ring Old", "max_price": 1000000, "item_ids": ["ab94d117"]},
    {"name": "Fire Ring Old", "max_price": 500000, "item_ids": ["6e2b7a14"]},
    {"name": "Fire Ring +0", "max_price": 12000000, "item_ids": ["bc49b913"]},
    {"name": "Fire Ring +1", "max_price": 220000000, "item_ids": ["894bb913"]},
    {"name": "Fire Ring +2", "max_price": 220000000, "item_ids": ["8a4bb913"]},
    {"name": "Fire Ring +3", "max_price": 220000000, "item_ids": ["8b4bb913"]},
    {"name": "Frozen Ring Old", "max_price": 500000, "item_ids": ["3f987e14"]},
    {"name": "Frozen Ring +0", "max_price": 1000000, "item_ids": ["cd70b913"]},
    {"name": "Thunder Ring Old", "max_price": 500000, "item_ids": ["10058314"]},
    {"name": "Essence Pendant Old", "max_price": 500000, "item_ids": ["17786814"]},
    {"name": "Essence Pendant +0", "max_price": 12000000, "item_ids": ["247e1413"]},
    {"name": "Essence Pendant +1", "max_price": 50000000, "item_ids": ["e77e1413"]},
    {"name": "Essence Pendant +2", "max_price": 220000000, "item_ids": ["e87e1413"]},
    {"name": "Essence Pendant +3", "max_price": 220000000, "item_ids": ["e97e1413"]},
    {"name": "Holy Pendant Old", "max_price": 500000, "item_ids": ["e8e46c14"]},
    {"name": "Holy Pendant +0", "max_price": 15000000, "item_ids": ["257e1413"]},
    {"name": "Holy Pendant +1", "max_price": 220000000, "item_ids": ["f17e1413"]},
    {"name": "Holy Pendant +2", "max_price": 220000000, "item_ids": ["f27e1413"]},
    {"name": "Holy Pendant +3", "max_price": 220000000, "item_ids": ["f37e1413"]},
    {"name": "Courage Pendant Old", "max_price": 1000000, "item_ids": ["460b6414"]},
    {"name": "Courage Pendant +0", "max_price": 10000000, "item_ids": ["237e1413"]},
    {"name": "Courage Pendant +1", "max_price": 220000000, "item_ids": ["dd7e1413"]},
    {"name": "Courage Pendant +2", "max_price": 220000000, "item_ids": ["de7e1413"]},
    {"name": "Courage Pendant +3", "max_price": 220000000, "item_ids": ["df7e1413"]},
    {"name": "Elderwood Belt Old", "max_price": 1000000, "item_ids": ["97de8b14"]},
    {"name": "Elderwood Belt +0", "max_price": 25000000, "item_ids": ["013f4a14"]},
    {"name": "Elderwood Belt +1", "max_price": 220000000, "item_ids": ["3f404a14"]},
    {"name": "Elderwood Belt +2", "max_price": 220000000, "item_ids": ["40404a14"]},
    {"name": "Elderwood Belt +3", "max_price": 220000000, "item_ids": ["41404a14"]},
    {"name": "Skull Belt Old", "max_price": 500000, "item_ids": ["684b9014"]},
    {"name": "Skull Belt +0", "max_price": 1000000, "item_ids": ["033f4a14"]},
    {"name": "Skull Belt +1", "max_price": 30000000, "item_ids": ["53404a14"]},
    {"name": "Skull Belt +2", "max_price": 150000000, "item_ids": ["54404a14"]},
    {"name": "Skull Belt +3", "max_price": 220000000, "item_ids": ["55404a14"]},
    {"name": "Belt of STR Old", "max_price": 1000000, "item_ids": ["58ef4b14"]},
    {"name": "Belt of STR +0", "max_price": 20000000, "item_ids": ["9ec54b14"]},
    {"name": "Belt of STR +1", "max_price": 220000000, "item_ids": ["c1c64b14"]},
    {"name": "Belt of STR +2", "max_price": 220000000, "item_ids": ["c2c64b14"]},
    {"name": "Belt of STR +3", "max_price": 220000000, "item_ids": ["c3c64b14"]},
    {"name": "Elfen Earring Old", "max_price": 1000000, "item_ids": ["ac278412"]},
    {"name": "Elfen Earring +0", "max_price": 30000000, "item_ids": ["ba888312"]},
    {"name": "Elfen Earring +1", "max_price": 220000000, "item_ids": ["4b898312"]},
    {"name": "Elfen Earring +2", "max_price": 220000000, "item_ids": ["4c898312"]},
    {"name": "Elfen Earring +3", "max_price": 220000000, "item_ids": ["4d898312"]},
    {"name": "Berserker Earring Old", "max_price": 1000000, "item_ids": ["f0528212"]},
    {"name": "Berserker Earring +1", "max_price": 220000000, "item_ids": ["d3028212"]},
    {"name": "Berserker Earring +2", "max_price": 220000000, "item_ids": ["d4028212"]},
    {"name": "Berserker Earring +3", "max_price": 220000000, "item_ids": ["d5028212"]},
    {"name": "Courage Earring Old", "max_price": 1000000, "item_ids": ["5bf38012"]},
    {"name": "Courage Earring +0", "max_price": 50000000, "item_ids": ["797b8012"]},
    {"name": "Courage Earring +1", "max_price": 220000000, "item_ids": ["017c8012"]},
    {"name": "Courage Earring +2", "max_price": 220000000, "item_ids": ["027c8012"]},
    {"name": "Courage Earring +3", "max_price": 220000000, "item_ids": ["037c8012"]},
    {"name": "Shadow Earring +0", "max_price": 500000, "item_ids": []},
    {"name": "Shaman Silver Earring +0", "max_price": 50000000, "item_ids": ["7b7b8012"]},
    {"name": "Shaman Silver Earring +1", "max_price": 150000000, "item_ids": ["157c8012"]},
    {"name": "Shaman Silver Earring +2", "max_price": 220000000, "item_ids": ["167c8012"]},
    {"name": "Shaman Silver Earring +3", "max_price": 220000000, "item_ids": ["177c8012"]},
    {"name": "Rogue Silver Earring +0", "max_price": 70000000, "item_ids": ["b6888312"]},
    {"name": "Rogue Silver Earring +1", "max_price": 220000000, "item_ids": ["23898312"]},
    {"name": "Rogue Silver Earring +2", "max_price": 220000000, "item_ids": ["24898312"]},
    {"name": "Rogue Silver Earring +3", "max_price": 220000000, "item_ids": ["25898312"]},
    {"name": "Hero Ring Old", "max_price": 1000000, "item_ids": ["9dbe7514"]},
    {"name": "Hero Ring +0", "max_price": 70000000, "item_ids": ["2f15ad13"]},
    {"name": "Hero Ring +1", "max_price": 220000000, "item_ids": ["5d15ad13"]},
    {"name": "Hero Ring +2", "max_price": 220000000, "item_ids": ["5e15ad13"]},
    {"name": "Hero Ring +3", "max_price": 220000000, "item_ids": ["5f15ad13"]},
    {"name": "Blue Drake Neck +0", "max_price": 1000000, "item_ids": ["501f1c13"]},
    {"name": "Amulet Of Evil Old", "max_price": 1000000, "item_ids": ["b3851b13"]},
    {"name": "Amulet Of Evil +0", "max_price": 95000000, "item_ids": ["a6981a13"]},
    {"name": "Amulet Of Evil +1", "max_price": 220000000, "item_ids": ["7b991a13"]},
    {"name": "Amulet Of Evil +2", "max_price": 220000000, "item_ids": ["7c991a13"]},
    {"name": "Amulet Of Evil +3", "max_price": 220000000, "item_ids": ["7d991a13"]},
    {"name": "Elder Necklace Old", "max_price": 1000000, "item_ids": ["37031813"]},
    {"name": "Amulet of Divinity Old", "max_price": 300000, "item_ids": ["58c21a13"]},
    {"name": "Red Drake Neck Old", "max_price": 300000, "item_ids": ["4c2a1813"]},
    {"name": "Str Necklace Old", "max_price": 1000000, "item_ids": ["10701c13"]},
    {"name": "Str Necklace +0", "max_price": 20000000, "item_ids": ["471f1c13"]},
    {"name": "Str Necklace +1", "max_price": 220000000, "item_ids": ["25201c13"]},
    {"name": "Str Necklace +2", "max_price": 220000000, "item_ids": ["26201c13"]},
    {"name": "Str Necklace +3", "max_price": 220000000, "item_ids": ["27201c13"]},
    {"name": "Secret Power Ring Old", "max_price": 500000, "item_ids": ["8047b213"]},
    {"name": "Secret Power Ring +0", "max_price": 30000000, "item_ids": ["15a9b113"]},
    {"name": "Secret Power Ring +1", "max_price": 220000000, "item_ids": ["79a9b113"]},
    {"name": "Secret Power Ring +2", "max_price": 220000000, "item_ids": ["7aa9b113"]},
    {"name": "Secret Power Ring +3", "max_price": 220000000, "item_ids": ["7ba9b113"]},
    {"name": "Elderwood Ring Old", "max_price": 1000000, "item_ids": ["b754b513"]},
    {"name": "Elderwood Ring +0", "max_price": 100000000, "item_ids": ["59b6b413"]},
    {"name": "Elderwood Ring +1", "max_price": 220000000, "item_ids": ["e1b6b413"]},
    {"name": "Elderwood Ring +2", "max_price": 220000000, "item_ids": ["e2b6b413"]},
    {"name": "Elderwood Ring +3", "max_price": 220000000, "item_ids": ["e3b6b413"]},
    {"name": "Ring of Shadow Old", "max_price": 5000000, "item_ids": ["cc517114"]},
    {"name": "Ring of Shadow +0", "max_price": 220000000, "item_ids": ["71b1ad13"]},
    {"name": "Ring of Shadow +1", "max_price": 220000000, "item_ids": ["b1b1ad13"]},
    {"name": "Ring of Shadow +2", "max_price": 220000000, "item_ids": ["b2b1ad13"]},
    {"name": "Ring of Shadow +3", "max_price": 220000000, "item_ids": ["b3b1ad13"]},
    {"name": "Hero Earring +0", "max_price": 20000000, "item_ids": ["75f47e12"]},
    {"name": "Hero Earring +1", "max_price": 40000000, "item_ids": ["01f67e12"]},
    {"name": "Hero Earring +2", "max_price": 220000000, "item_ids": ["02f67e12"]},
    {"name": "Hero Earring +3", "max_price": 220000000, "item_ids": ["03f67e12"]},
    {"name": "Old Ring of the Dragon Fire Old", "max_price": 220000000, "item_ids": ["c8dcb413"]},
    {"name": "Old Ring of the Dragon Fire +0", "max_price": 1000000000, "item_ids": ["6eddb413"]},
    {"name": "Old Ring of the Dragon Ice Old", "max_price": 220000000, "item_ids": ["3f805214"]},
    {"name": "Old Ring of the Dragon Light Old", "max_price": 220000000, "item_ids": ["29845214"]},
    {"name": "Old Ring of the Dragon Light +0", "max_price": 1000000000, "item_ids": ["3a875214"]},
    {"name": "Legender Belt +0", "max_price": 220000000, "item_ids": ["fd3e4a14", "16404a14"]},
    {"name": "Legender Belt +1", "max_price": 2500000000, "item_ids": ["17404a14"]},
    {"name": "Legender Belt +2", "max_price": 5000000000, "item_ids": ["18404a14"]},
    {"name": "Legender Belt +3", "max_price": 6000000000, "item_ids": ["19404a14"]},
    {"name": "STR Neck of Dragon +0", "max_price": 10000000000, "item_ids": ["6e8b1713"]},
    {"name": "Belt of Dragon +0", "max_price": 2200000000, "item_ids": ["3b4c4d14"]},
    {"name": "Warrior Holy Titan Helmet +5", "max_price": 5000000, "item_ids": ["475b470c", "3d5b470c"]},
    {"name": "Warrior Holy Titan Helmet +6", "max_price": 10000000, "item_ids": ["485b470c", "3e5b470c"]},
    {"name": "Warrior Holy Titan Helmet +7", "max_price": 30000000, "item_ids": ["3f5b470c", "495b470c"]},
    {"name": "Warrior Holy Titan Helmet +8", "max_price": 220000000, "item_ids": ["4a5b470c", "405b470c"]},
    {"name": "Warrior Holy Titan Helmet +9", "max_price": 3000000000, "item_ids": ["415b470c", "4b5b470c"]},
    {"name": "Warrior Holy Titan Helmet +10", "max_price": 3000000000, "item_ids": ["425b470c", "4c5b470c"]},
    {"name": "Warrior Holy Titan Helmet Reb+1", "max_price": 30000000, "item_ids": ["b9f1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+2", "max_price": 30000000, "item_ids": ["baf1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+3", "max_price": 100000000, "item_ids": ["bbf1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+4", "max_price": 220000000, "item_ids": ["bcf1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+5", "max_price": 220000000, "item_ids": ["bdf1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+6", "max_price": 220000000, "item_ids": ["bef1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+7", "max_price": 220000000, "item_ids": ["bff1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+8", "max_price": 1000000000, "item_ids": ["c0f1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+9", "max_price": 1000000000, "item_ids": ["c1f1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+10", "max_price": 1000000000, "item_ids": ["c2f1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+11", "max_price": 3000000000, "item_ids": ["c3f1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+12", "max_price": 3000000000, "item_ids": ["c4f1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+13", "max_price": 3000000000, "item_ids": ["c5f1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+14", "max_price": 3000000000, "item_ids": ["c6f1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+15", "max_price": 3000000000, "item_ids": ["c7f1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+16", "max_price": 3000000000, "item_ids": ["c8f1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+17", "max_price": 3000000000, "item_ids": ["c9f1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+18", "max_price": 3000000000, "item_ids": ["caf1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+19", "max_price": 3000000000, "item_ids": ["cbf1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+20", "max_price": 3000000000, "item_ids": ["ccf1df0c"]},
    {"name": "Warrior Holy Titan Helmet Reb+21", "max_price": 3000000000, "item_ids": ["cdf1df0c"]},
    {"name": "Warrior Holy Titan Pauldron +5", "max_price": 5000000, "item_ids": ["6d53470c", "7753470c"]},
    {"name": "Warrior Holy Titan Pauldron +6", "max_price": 10000000, "item_ids": ["6e53470c", "7853470c"]},
    {"name": "Warrior Holy Titan Pauldron +7", "max_price": 30000000, "item_ids": ["7953470c", "6f53470c"]},
    {"name": "Warrior Holy Titan Pauldron +8", "max_price": 220000000, "item_ids": ["7053470c", "7a53470c"]},
    {"name": "Warrior Holy Titan Pauldron +9", "max_price": 3000000000, "item_ids": ["7b53470c", "7153470c"]},
    {"name": "Warrior Holy Titan Pauldron +10", "max_price": 3000000000, "item_ids": ["7c53470c", "7253470c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+1", "max_price": 30000000, "item_ids": ["e9e9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+2", "max_price": 30000000, "item_ids": ["eae9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+3", "max_price": 100000000, "item_ids": ["ebe9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+4", "max_price": 220000000, "item_ids": ["ece9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+5", "max_price": 220000000, "item_ids": ["ede9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+6", "max_price": 220000000, "item_ids": ["eee9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+7", "max_price": 220000000, "item_ids": ["efe9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+8", "max_price": 1000000000, "item_ids": ["f0e9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+9", "max_price": 1000000000, "item_ids": ["f1e9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+10", "max_price": 1000000000, "item_ids": ["f2e9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+11", "max_price": 3000000000, "item_ids": ["f3e9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+12", "max_price": 3000000000, "item_ids": ["f4e9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+13", "max_price": 3000000000, "item_ids": ["f5e9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+14", "max_price": 3000000000, "item_ids": ["f6e9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+15", "max_price": 3000000000, "item_ids": ["f7e9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+16", "max_price": 3000000000, "item_ids": ["f8e9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+17", "max_price": 3000000000, "item_ids": ["f9e9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+18", "max_price": 3000000000, "item_ids": ["fae9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+19", "max_price": 3000000000, "item_ids": ["fbe9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+20", "max_price": 3000000000, "item_ids": ["fce9df0c"]},
    {"name": "Warrior Holy Titan Pauldron Reb+21", "max_price": 3000000000, "item_ids": ["fde9df0c"]},
    {"name": "Warrior Holy Titan Pads +5", "max_price": 5000000, "item_ids": ["5557470c"]},
    {"name": "Warrior Holy Titan Pads +6", "max_price": 10000000, "item_ids": ["5657470c"]},
    {"name": "Warrior Holy Titan Pads +7", "max_price": 30000000, "item_ids": ["5757470c"]},
    {"name": "Warrior Holy Titan Pads +8", "max_price": 220000000, "item_ids": ["5857470c"]},
    {"name": "Warrior Holy Titan Pads +9", "max_price": 3000000000, "item_ids": ["5957470c"]},
    {"name": "Warrior Holy Titan Pads +10", "max_price": 3000000000, "item_ids": ["5a57470c"]},
    {"name": "Warrior Holy Titan Pads Reb+1", "max_price": 30000000, "item_ids": ["d1eddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+2", "max_price": 30000000, "item_ids": ["d2eddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+3", "max_price": 100000000, "item_ids": ["d3eddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+4", "max_price": 220000000, "item_ids": ["d4eddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+5", "max_price": 220000000, "item_ids": ["d5eddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+6", "max_price": 220000000, "item_ids": ["d6eddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+7", "max_price": 220000000, "item_ids": ["d7eddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+8", "max_price": 1000000000, "item_ids": ["d8eddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+9", "max_price": 1000000000, "item_ids": ["d9eddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+10", "max_price": 1000000000, "item_ids": ["daeddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+11", "max_price": 3000000000, "item_ids": ["dbeddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+12", "max_price": 3000000000, "item_ids": ["dceddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+13", "max_price": 3000000000, "item_ids": ["ddeddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+14", "max_price": 3000000000, "item_ids": ["deeddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+15", "max_price": 3000000000, "item_ids": ["dfeddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+16", "max_price": 3000000000, "item_ids": ["e0eddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+17", "max_price": 3000000000, "item_ids": ["e1eddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+18", "max_price": 3000000000, "item_ids": ["e2eddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+19", "max_price": 3000000000, "item_ids": ["e3eddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+20", "max_price": 3000000000, "item_ids": ["e4eddf0c"]},
    {"name": "Warrior Holy Titan Pads Reb+21", "max_price": 3000000000, "item_ids": ["e5eddf0c"]},
    {"name": "Warrior Holy Titan Boots +5", "max_price": 5000000, "item_ids": ["0d63470c"]},
    {"name": "Warrior Holy Titan Boots +6", "max_price": 10000000, "item_ids": ["0e63470c"]},
    {"name": "Warrior Holy Titan Boots +7", "max_price": 30000000, "item_ids": ["0f63470c"]},
    {"name": "Warrior Holy Titan Boots +8", "max_price": 220000000, "item_ids": ["1063470c"]},
    {"name": "Warrior Holy Titan Boots +9", "max_price": 3000000000, "item_ids": ["1163470c"]},
    {"name": "Warrior Holy Titan Boots +10", "max_price": 3000000000, "item_ids": ["1263470c"]},
    {"name": "Warrior Holy Titan Boots Reb+1", "max_price": 30000000, "item_ids": ["89f9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+2", "max_price": 30000000, "item_ids": ["8af9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+3", "max_price": 100000000, "item_ids": ["8bf9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+4", "max_price": 220000000, "item_ids": ["8cf9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+5", "max_price": 220000000, "item_ids": ["8df9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+6", "max_price": 220000000, "item_ids": ["8ef9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+7", "max_price": 220000000, "item_ids": ["8ff9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+8", "max_price": 1000000000, "item_ids": ["90f9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+9", "max_price": 1000000000, "item_ids": ["91f9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+10", "max_price": 1000000000, "item_ids": ["92f9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+11", "max_price": 3000000000, "item_ids": ["93f9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+12", "max_price": 3000000000, "item_ids": ["94f9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+13", "max_price": 3000000000, "item_ids": ["95f9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+14", "max_price": 3000000000, "item_ids": ["96f9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+15", "max_price": 3000000000, "item_ids": ["97f9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+16", "max_price": 3000000000, "item_ids": ["98f9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+17", "max_price": 3000000000, "item_ids": ["99f9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+18", "max_price": 3000000000, "item_ids": ["9af9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+19", "max_price": 3000000000, "item_ids": ["9bf9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+20", "max_price": 3000000000, "item_ids": ["9cf9df0c"]},
    {"name": "Warrior Holy Titan Boots Reb+21", "max_price": 3000000000, "item_ids": ["9df9df0c"]},
    {"name": "Warrior Holy Titan Gauntlets +5", "max_price": 5000000, "item_ids": ["255f470c", "2f5f470c"]},
    {"name": "Warrior Holy Titan Gauntlets +6", "max_price": 10000000, "item_ids": ["305f470c", "265f470c"]},
    {"name": "Warrior Holy Titan Gauntlets +7", "max_price": 30000000, "item_ids": ["315f470c", "275f470c"]},
    {"name": "Warrior Holy Titan Gauntlets +8", "max_price": 220000000, "item_ids": ["285f470c", "325f470c"]},
    {"name": "Warrior Holy Titan Gauntlets +9", "max_price": 3000000000, "item_ids": ["335f470c", "295f470c"]},
    {"name": "Warrior Holy Titan Gauntlets +10", "max_price": 3000000000, "item_ids": ["345f470c", "2a5f470c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+1", "max_price": 30000000, "item_ids": ["a1f5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+2", "max_price": 30000000, "item_ids": ["a2f5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+3", "max_price": 100000000, "item_ids": ["a3f5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+4", "max_price": 220000000, "item_ids": ["a4f5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+5", "max_price": 220000000, "item_ids": ["a5f5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+6", "max_price": 220000000, "item_ids": ["a6f5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+7", "max_price": 220000000, "item_ids": ["a7f5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+8", "max_price": 1000000000, "item_ids": ["a8f5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+9", "max_price": 1000000000, "item_ids": ["a9f5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+10", "max_price": 1000000000, "item_ids": ["aaf5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+11", "max_price": 3000000000, "item_ids": ["abf5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+12", "max_price": 3000000000, "item_ids": ["acf5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+13", "max_price": 3000000000, "item_ids": ["adf5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+14", "max_price": 3000000000, "item_ids": ["aef5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+15", "max_price": 3000000000, "item_ids": ["aff5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+16", "max_price": 3000000000, "item_ids": ["b0f5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+17", "max_price": 3000000000, "item_ids": ["b1f5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+18", "max_price": 3000000000, "item_ids": ["b2f5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+19", "max_price": 3000000000, "item_ids": ["b3f5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+20", "max_price": 3000000000, "item_ids": ["b4f5df0c"]},
    {"name": "Warrior Holy Titan Gauntlets Reb+21", "max_price": 3000000000, "item_ids": ["b5f5df0c"]},
    {"name": "Warrior Titan Helmet +6", "max_price": 3000000, "item_ids": ["fe18380c", "0819380c"]},
    {"name": "Warrior Titan Helmet +7", "max_price": 10000000, "item_ids": ["ff18380c", "0919380c"]},
    {"name": "Warrior Titan Helmet +8", "max_price": 220000000, "item_ids": ["0a19380c", "0018380c"]},
    {"name": "Warrior Titan Helmet +9", "max_price": 1000000000, "item_ids": ["0b19380c", "0118380c"]},
    {"name": "Warrior Titan Helmet +10", "max_price": 10000000003000000000, "item_ids": ["0c19380c", "0218380c"]},
    {"name": "Warrior Titan Helmet Reb+1", "max_price": 10000000, "item_ids": ["79afd00c"]},
    {"name": "Warrior Titan Helmet Reb+2", "max_price": 10000000, "item_ids": ["7aafd00c"]},
    {"name": "Warrior Titan Helmet Reb+3", "max_price": 40000000, "item_ids": ["7bafd00c"]},
    {"name": "Warrior Titan Helmet Reb+4", "max_price": 40000000, "item_ids": ["7cafd00c"]},
    {"name": "Warrior Titan Helmet Reb+5", "max_price": 220000000, "item_ids": ["7dafd00c"]},
    {"name": "Warrior Titan Helmet Reb+6", "max_price": 220000000, "item_ids": ["7eafd00c"]},
    {"name": "Warrior Titan Helmet Reb+7", "max_price": 220000000, "item_ids": ["7fafd00c"]},
    {"name": "Warrior Titan Helmet Reb+8", "max_price": 700000000, "item_ids": ["80afd00c"]},
    {"name": "Warrior Titan Helmet Reb+9", "max_price": 700000000, "item_ids": ["81afd00c"]},
    {"name": "Warrior Titan Helmet Reb+10", "max_price": 1000000000, "item_ids": ["82afd00c"]},
    {"name": "Warrior Titan Helmet Reb+11", "max_price": 1000000000, "item_ids": ["83afd00c"]},
    {"name": "Warrior Titan Helmet Reb+12", "max_price": 1000000000, "item_ids": ["84afd00c"]},
    {"name": "Warrior Titan Helmet Reb+13", "max_price": 1000000000, "item_ids": ["85afd00c"]},
    {"name": "Warrior Titan Helmet Reb+14", "max_price": 1000000000, "item_ids": ["86afd00c"]},
    {"name": "Warrior Titan Helmet Reb+15", "max_price": 1000000000, "item_ids": ["87afd00c"]},
    {"name": "Warrior Titan Helmet Reb+16", "max_price": 1000000000, "item_ids": ["88afd00c"]},
    {"name": "Warrior Titan Helmet Reb+17", "max_price": 1000000000, "item_ids": ["89afd00c"]},
    {"name": "Warrior Titan Helmet Reb+18", "max_price": 1000000000, "item_ids": ["8aafd00c"]},
    {"name": "Warrior Titan Helmet Reb+19", "max_price": 1000000000, "item_ids": ["8bafd00c"]},
    {"name": "Warrior Titan Helmet Reb+20", "max_price": 1000000000, "item_ids": ["8cafd00c"]},
    {"name": "Warrior Titan Helmet Reb+21", "max_price": 1000000000, "item_ids": ["8dafd00c"]},
    {"name": "Warrior Titan Pauldron +6", "max_price": 3000000, "item_ids": ["2e11380c", "3811380c"]},
    {"name": "Warrior Titan Pauldron +7", "max_price": 10000000, "item_ids": ["3911380c", "2f11380c"]},
    {"name": "Warrior Titan Pauldron +8", "max_price": 220000000, "item_ids": ["3011380c", "3a11380c"]},
    {"name": "Warrior Titan Pauldron +9", "max_price": 1000000000, "item_ids": ["3b11380c", "3111380c"]},
    {"name": "Warrior Titan Pauldron +10", "max_price": 1000000000, "item_ids": ["3c11380c", "3211380c"]},
    {"name": "Warrior Titan Pauldron Reb+1", "max_price": 10000000, "item_ids": ["a9a7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+2", "max_price": 10000000, "item_ids": ["aaa7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+3", "max_price": 40000000, "item_ids": ["aba7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+4", "max_price": 40000000, "item_ids": ["aca7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+5", "max_price": 220000000, "item_ids": ["ada7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+6", "max_price": 220000000, "item_ids": ["aea7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+7", "max_price": 220000000, "item_ids": ["afa7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+8", "max_price": 700000000, "item_ids": ["b0a7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+9", "max_price": 700000000, "item_ids": ["b1a7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+10", "max_price": 1000000000, "item_ids": ["b2a7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+11", "max_price": 1000000000, "item_ids": ["b3a7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+12", "max_price": 1000000000, "item_ids": ["b4a7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+13", "max_price": 1000000000, "item_ids": ["b5a7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+14", "max_price": 1000000000, "item_ids": ["b6a7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+15", "max_price": 1000000000, "item_ids": ["b7a7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+16", "max_price": 1000000000, "item_ids": ["b8a7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+17", "max_price": 1000000000, "item_ids": ["b9a7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+18", "max_price": 1000000000, "item_ids": ["baa7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+19", "max_price": 1000000000, "item_ids": ["bba7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+20", "max_price": 1000000000, "item_ids": ["bca7d00c"]},
    {"name": "Warrior Titan Pauldron Reb+21", "max_price": 1000000000, "item_ids": ["bda7d00c"]},
    {"name": "Warrior Titan Pads +6", "max_price": 3000000, "item_ids": ["2015380c", "1615380c"]},
    {"name": "Warrior Titan Pads +7", "max_price": 10000000, "item_ids": ["2115380c", "1715380c"]},
    {"name": "Warrior Titan Pads +8", "max_price": 220000000, "item_ids": ["2215380c", "1815380c"]},
    {"name": "Warrior Titan Pads +9", "max_price": 1000000000, "item_ids": ["2315380c", "1915380c"]},
    {"name": "Warrior Titan Pads +10", "max_price": 1000000000, "item_ids": ["2415380c", "1a15380c"]},
    {"name": "Warrior Titan Pads Reb+1", "max_price": 10000000, "item_ids": ["91abd00c"]},
    {"name": "Warrior Titan Pads Reb+2", "max_price": 10000000, "item_ids": ["92abd00c"]},
    {"name": "Warrior Titan Pads Reb+3", "max_price": 40000000, "item_ids": ["93abd00c"]},
    {"name": "Warrior Titan Pads Reb+4", "max_price": 40000000, "item_ids": ["94abd00c"]},
    {"name": "Warrior Titan Pads Reb+5", "max_price": 220000000, "item_ids": ["95abd00c"]},
    {"name": "Warrior Titan Pads Reb+6", "max_price": 220000000, "item_ids": ["96abd00c"]},
    {"name": "Warrior Titan Pads Reb+7", "max_price": 220000000, "item_ids": ["97abd00c"]},
    {"name": "Warrior Titan Pads Reb+8", "max_price": 700000000, "item_ids": ["98abd00c"]},
    {"name": "Warrior Titan Pads Reb+9", "max_price": 1000000000, "item_ids": ["99abd00c"]},
    {"name": "Warrior Titan Pads Reb+10", "max_price": 1000000000, "item_ids": ["9aabd00c"]},
    {"name": "Warrior Titan Pads Reb+11", "max_price": 1000000000, "item_ids": ["9babd00c"]},
    {"name": "Warrior Titan Pads Reb+12", "max_price": 1000000000, "item_ids": ["9cabd00c"]},
    {"name": "Warrior Titan Pads Reb+13", "max_price": 1000000000, "item_ids": ["9dabd00c"]},
    {"name": "Warrior Titan Pads Reb+14", "max_price": 1000000000, "item_ids": ["9eabd00c"]},
    {"name": "Warrior Titan Pads Reb+15", "max_price": 1000000000, "item_ids": ["9fabd00c"]},
    {"name": "Warrior Titan Pads Reb+16", "max_price": 1000000000, "item_ids": ["a0abd00c"]},
    {"name": "Warrior Titan Pads Reb+17", "max_price": 1000000000, "item_ids": ["a1abd00c"]},
    {"name": "Warrior Titan Pads Reb+18", "max_price": 1000000000, "item_ids": ["a2abd00c"]},
    {"name": "Warrior Titan Pads Reb+19", "max_price": 1000000000, "item_ids": ["a3abd00c"]},
    {"name": "Warrior Titan Pads Reb+20", "max_price": 1000000000, "item_ids": ["a4abd00c"]},
    {"name": "Warrior Titan Pads Reb+21", "max_price": 1000000000, "item_ids": ["a5abd00c"]},
    {"name": "Warrior Titan Boots +6", "max_price": 3000000, "item_ids": ["ce20380c", "d820380c"]},
    {"name": "Warrior Titan Boots +7", "max_price": 10000000, "item_ids": ["d920380c", "cf20380c"]},
    {"name": "Warrior Titan Boots +8", "max_price": 220000000, "item_ids": ["d020380c", "da20380c"]},
    {"name": "Warrior Titan Boots +9", "max_price": 1000000000, "item_ids": ["db20380c", "d120380c"]},
    {"name": "Warrior Titan Boots +10", "max_price": 1000000000, "item_ids": ["dc20380c", "d220380c"]},
    {"name": "Warrior Titan Boots Reb+1", "max_price": 10000000, "item_ids": ["49b7d00c"]},
    {"name": "Warrior Titan Boots Reb+2", "max_price": 10000000, "item_ids": ["4ab7d00c"]},
    {"name": "Warrior Titan Boots Reb+3", "max_price": 40000000, "item_ids": ["4bb7d00c"]},
    {"name": "Warrior Titan Boots Reb+4", "max_price": 40000000, "item_ids": ["4cb7d00c"]},
    {"name": "Warrior Titan Boots Reb+5", "max_price": 220000000, "item_ids": ["4db7d00c"]},
    {"name": "Warrior Titan Boots Reb+6", "max_price": 220000000, "item_ids": ["4eb7d00c"]},
    {"name": "Warrior Titan Boots Reb+7", "max_price": 220000000, "item_ids": ["4fb7d00c"]},
    {"name": "Warrior Titan Boots Reb+8", "max_price": 700000000, "item_ids": ["50b7d00c"]},
    {"name": "Warrior Titan Boots Reb+9", "max_price": 1000000000, "item_ids": ["51b7d00c"]},
    {"name": "Warrior Titan Boots Reb+10", "max_price": 1000000000, "item_ids": ["52b7d00c"]},
    {"name": "Warrior Titan Boots Reb+11", "max_price": 1000000000, "item_ids": ["53b7d00c"]},
    {"name": "Warrior Titan Boots Reb+12", "max_price": 1000000000, "item_ids": ["54b7d00c"]},
    {"name": "Warrior Titan Boots Reb+13", "max_price": 1000000000, "item_ids": ["55b7d00c"]},
    {"name": "Warrior Titan Boots Reb+14", "max_price": 1000000000, "item_ids": ["56b7d00c"]},
    {"name": "Warrior Titan Boots Reb+15", "max_price": 1000000000, "item_ids": ["57b7d00c"]},
    {"name": "Warrior Titan Boots Reb+16", "max_price": 1000000000, "item_ids": ["58b7d00c"]},
    {"name": "Warrior Titan Boots Reb+17", "max_price": 1000000000, "item_ids": ["59b7d00c"]},
    {"name": "Warrior Titan Boots Reb+18", "max_price": 1000000000, "item_ids": ["5ab7d00c"]},
    {"name": "Warrior Titan Boots Reb+19", "max_price": 1000000000, "item_ids": ["5bb7d00c"]},
    {"name": "Warrior Titan Boots Reb+20", "max_price": 1000000000, "item_ids": ["5cb7d00c"]},
    {"name": "Warrior Titan Boots Reb+21", "max_price": 1000000000, "item_ids": ["5db7d00c"]},
    {"name": "Warrior Titan Gauntlets +6", "max_price": 3000000, "item_ids": ["e61c380c", "f01c380c"]},
    {"name": "Warrior Titan Gauntlets +7", "max_price": 10000000, "item_ids": ["f11c380c", "e71c380c"]},
    {"name": "Warrior Titan Gauntlets +8", "max_price": 220000000, "item_ids": ["e81c380c", "f21c380c"]},
    {"name": "Warrior Titan Gauntlets +9", "max_price": 1000000000, "item_ids": ["f31c380c", "e91c380c"]},
    {"name": "Warrior Titan Gauntlets +10", "max_price": 1000000000, "item_ids": ["f41c380c", "ea1c380c"]},
    {"name": "Warrior Titan Gauntlets Reb+1", "max_price": 10000000, "item_ids": ["61b3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+2", "max_price": 10000000, "item_ids": ["62b3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+3", "max_price": 40000000, "item_ids": ["63b3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+4", "max_price": 40000000, "item_ids": ["64b3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+5", "max_price": 220000000, "item_ids": ["65b3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+6", "max_price": 220000000, "item_ids": ["66b3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+7", "max_price": 220000000, "item_ids": ["67b3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+8", "max_price": 700000000, "item_ids": ["68b3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+9", "max_price": 1000000000, "item_ids": ["69b3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+10", "max_price": 1000000000, "item_ids": ["6ab3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+11", "max_price": 1000000000, "item_ids": ["6bb3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+12", "max_price": 1000000000, "item_ids": ["6cb3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+13", "max_price": 1000000000, "item_ids": ["6db3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+14", "max_price": 1000000000, "item_ids": ["6eb3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+15", "max_price": 1000000000, "item_ids": ["6fb3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+16", "max_price": 1000000000, "item_ids": ["70b3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+17", "max_price": 1000000000, "item_ids": ["71b3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+18", "max_price": 1000000000, "item_ids": ["72b3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+19", "max_price": 1000000000, "item_ids": ["73b3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+20", "max_price": 1000000000, "item_ids": ["74b3d00c"]},
    {"name": "Warrior Titan Gauntlets Reb+21", "max_price": 1000000000, "item_ids": ["75b3d00c"]},
    {"name": "Warrior Elder Armor Boots +5", "max_price": 100000000, "item_ids": ["4d48381e", "5748381e"]},
    {"name": "Warrior Elder Armor Boots +6", "max_price": 100000000, "item_ids": ["4e48381e", "5848381e"]},
    {"name": "Warrior Elder Armor Boots +7", "max_price": 220000000, "item_ids": ["5948381e", "4f48381e"]},
    {"name": "Warrior Elder Armor Boots +8", "max_price": 220000000, "item_ids": ["5048381e", "5a48381e"]},
    {"name": "Warrior Elder Armor Boots Reb+1", "max_price": 220000000, "item_ids": ["c9ded01e"]},
    {"name": "Warrior Elder Armor Boots Reb+2", "max_price": 220000000, "item_ids": ["caded01e"]},
    {"name": "Warrior Elder Armor Boots Reb+3", "max_price": 500000000, "item_ids": ["cbded01e"]},
    {"name": "Warrior Elder Armor Boots Reb+4", "max_price": 1000000000, "item_ids": ["ccded01e"]},
    {"name": "Warrior Elder Armor Boots Reb+5", "max_price": 3000000000, "item_ids": ["cdded01e"]},
    {"name": "Warrior Elder Armor Helmet +5", "max_price": 100000000, "item_ids": ["7d40381e"]},
    {"name": "Warrior Elder Armor Helmet +6", "max_price": 100000000, "item_ids": ["7e40381e"]},
    {"name": "Warrior Elder Armor Helmet +7", "max_price": 220000000, "item_ids": ["7f40381e"]},
    {"name": "Warrior Elder Armor Helmet +8", "max_price": 220000000, "item_ids": ["8040381e"]},
    {"name": "Warrior Elder Armor Helmet Reb+1", "max_price": 220000000, "item_ids": ["f9d6d01e"]},
    {"name": "Warrior Elder Armor Helmet Reb+2", "max_price": 220000000, "item_ids": ["fad6d01e"]},
    {"name": "Warrior Elder Armor Helmet Reb+3", "max_price": 500000000, "item_ids": ["fbd6d01e"]},
    {"name": "Warrior Elder Armor Helmet Reb+4", "max_price": 1000000000, "item_ids": ["fcd6d01e"]},
    {"name": "Warrior Elder Armor Helmet Reb+5", "max_price": 3000000000, "item_ids": ["fdd6d01e"]},
    {"name": "Warrior Elder Armor Pauldron +5", "max_price": 100000000, "item_ids": ["ad38381e", "b738381e"]},
    {"name": "Warrior Elder Armor Pauldron +6", "max_price": 100000000, "item_ids": ["ae38381e", "b838381e"]},
    {"name": "Warrior Elder Armor Pauldron +7", "max_price": 220000000, "item_ids": ["b938381e", "af38381e"]},
    {"name": "Warrior Elder Armor Pauldron +8", "max_price": 220000000, "item_ids": ["b038381e", "ba38381e"]},
    {"name": "Warrior Elder Armor Pants +5", "max_price": 100000000, "item_ids": ["953c381e"]},
    {"name": "Warrior Elder Armor Pants +6", "max_price": 100000000, "item_ids": ["963c381e"]},
    {"name": "Warrior Elder Armor Pants +7", "max_price": 220000000, "item_ids": ["973c381e"]},
    {"name": "Warrior Elder Armor Pants +8", "max_price": 220000000, "item_ids": ["983c381e"]},
    {"name": "Warrior Elder Armor Gauntlets +5", "max_price": 100000000, "item_ids": ["6f44381e", "6544381e"]},
    {"name": "Warrior Elder Armor Gauntlets +6", "max_price": 100000000, "item_ids": ["7044381e", "6644381e"]},
    {"name": "Warrior Elder Armor Gauntlets +7", "max_price": 220000000, "item_ids": ["7144381e", "6744381e"]},
    {"name": "Warrior Elder Armor Gauntlets +8", "max_price": 220000000, "item_ids": ["7244381e", "6844381e"]},
    {"name": "Rogue Holy Titan Helmet +5", "max_price": 5000000, "item_ids": ["3bb7a90e", "3db5a90e"]},
    {"name": "Rogue Holy Titan Helmet +6", "max_price": 10000000, "item_ids": ["3cb7a90e", "3eb5a90e"]},
    {"name": "Rogue Holy Titan Helmet +7", "max_price": 30000000, "item_ids": ["3db7a90e", "3fb5a90e"]},
    {"name": "Rogue Holy Titan Helmet +8", "max_price": 220000000, "item_ids": ["3eb7a90e", "40b5a90e"]},
    {"name": "Rogue Holy Titan Helmet +9", "max_price": 5000000000, "item_ids": ["3fb7a90e", "41b5a90e"]},
    {"name": "Rogue Holy Titan Helmet +10", "max_price": 5000000000, "item_ids": ["40b7a90e", "42b5a90e"]},
    {"name": "Rogue Holy Titan Helmet Reb+1", "max_price": 30000000, "item_ids": ["f54b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+2", "max_price": 30000000, "item_ids": ["f64b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+3", "max_price": 100000000, "item_ids": ["f74b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+4", "max_price": 220000000, "item_ids": ["f84b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+5", "max_price": 220000000, "item_ids": ["f94b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+6", "max_price": 500000000, "item_ids": ["fa4b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+7", "max_price": 500000000, "item_ids": ["fb4b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+8", "max_price": 1000000000, "item_ids": ["fc4b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+9", "max_price": 1000000000, "item_ids": ["fd4b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+10", "max_price": 5000000000, "item_ids": ["fe4b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+11", "max_price": 5000000000, "item_ids": ["ff4b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+12", "max_price": 5000000000, "item_ids": ["004b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+13", "max_price": 5000000000, "item_ids": ["014b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+14", "max_price": 5000000000, "item_ids": ["024b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+15", "max_price": 5000000000, "item_ids": ["034b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+16", "max_price": 5000000000, "item_ids": ["044b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+17", "max_price": 5000000000, "item_ids": ["054b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+18", "max_price": 5000000000, "item_ids": ["064b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+19", "max_price": 5000000000, "item_ids": ["074b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+20", "max_price": 5000000000, "item_ids": ["084b420f"]},
    {"name": "Rogue Holy Titan Helmet Reb+21", "max_price": 5000000000, "item_ids": ["094b420f"]},
    {"name": "Rogue Holy Titan Pauldron +5", "max_price": 5000000, "item_ids": ["6dada90e", "6bafa90e"]},
    {"name": "Rogue Holy Titan Pauldron +6", "max_price": 10000000, "item_ids": ["6eada90e", "6cafa90e"]},
    {"name": "Rogue Holy Titan Pauldron +7", "max_price": 30000000, "item_ids": ["6fada90e", "6dafa90e"]},
    {"name": "Rogue Holy Titan Pauldron +8", "max_price": 220000000, "item_ids": ["70ada90e", "6eafa90e"]},
    {"name": "Rogue Holy Titan Pauldron +9", "max_price": 5000000000, "item_ids": ["71ada90e", "6fafa90e"]},
    {"name": "Rogue Holy Titan Pauldron +10", "max_price": 5000000000, "item_ids": ["72ada90e", "70afa90e"]},
    {"name": "Rogue Holy Titan Pauldron Reb+1", "max_price": 30000000, "item_ids": ["2544420f"]},
    {"name": "Rogue Holy Titan Pauldron Reb+2", "max_price": 30000000, "item_ids": ["2644420f"]},
    {"name": "Rogue Holy Titan Pauldron Reb+3", "max_price": 100000000, "item_ids": ["2744420f"]},
    {"name": "Rogue Holy Titan Pauldron Reb+4", "max_price": 220000000, "item_ids": ["2844420f"]},
    {"name": "Rogue Holy Titan Pauldron Reb+5", "max_price": 220000000, "item_ids": ["2944420f"]},
    {"name": "Rogue Holy Titan Pauldron Reb+6", "max_price": 500000000, "item_ids": ["2a44420f"]},
    {"name": "Rogue Holy Titan Pauldron Reb+7", "max_price": 500000000, "item_ids": ["2b44420f"]},
    {"name": "Rogue Holy Titan Pauldron Reb+9", "max_price": 1000000000, "item_ids": ["2d44420f"]},
    {"name": "Rogue Holy Titan Pauldron Reb+11", "max_price": 5000000000, "item_ids": ["2f44420f"]},
    {"name": "Rogue Holy Titan Pauldron Reb+12", "max_price": 5000000000, "item_ids": ["3044420f"]},
    {"name": "Rogue Holy Titan Pauldron Reb+13", "max_price": 5000000000, "item_ids": ["3144420f"]},
    {"name": "Rogue Holy Titan Pauldron Reb+14", "max_price": 5000000000, "item_ids": ["3244420f"]},
    {"name": "Rogue Holy Titan Pauldron Reb+15", "max_price": 5000000000, "item_ids": ["3344420f"]},
    {"name": "Rogue Holy Titan Pauldron Reb+16", "max_price": 5000000000, "item_ids": ["3444420f"]},
    {"name": "Rogue Holy Titan Pauldron Reb+17", "max_price": 5000000000, "item_ids": ["3544420f"]},
    {"name": "Rogue Holy Titan Pauldron Reb+18", "max_price": 5000000000, "item_ids": ["3644420f"]},
    {"name": "Rogue Holy Titan Pauldron Reb+19", "max_price": 5000000000, "item_ids": ["3744420f"]},
    {"name": "Rogue Holy Titan Pauldron Reb+20", "max_price": 5000000000, "item_ids": ["3844420f"]},
    {"name": "Rogue Holy Titan Pauldron Reb+21", "max_price": 5000000000, "item_ids": ["3944420f"]},
    {"name": "Rogue Holy Titan Pads +5", "max_price": 5000000, "item_ids": ["53b3a90e", "55b1a90e"]},
    {"name": "Rogue Holy Titan Pads +6", "max_price": 10000000, "item_ids": ["54b3a90e", "56b1a90e"]},
    {"name": "Rogue Holy Titan Pads +7", "max_price": 30000000, "item_ids": ["57b1a90e", "55b3a90e"]},
    {"name": "Rogue Holy Titan Pads +8", "max_price": 220000000, "item_ids": ["56b3a90e", "58b1a90e"]},
    {"name": "Rogue Holy Titan Pads +9", "max_price": 5000000000, "item_ids": ["59b1a90e", "57b3a90e"]},
    {"name": "Rogue Holy Titan Pads +10", "max_price": 5000000000, "item_ids": ["5ab1a90e", "58b3a90e"]},
    {"name": "Rogue Holy Titan Pads Reb+1", "max_price": 30000000, "item_ids": ["0d48420f"]},
    {"name": "Rogue Holy Titan Pads Reb+2", "max_price": 30000000, "item_ids": ["0e48420f"]},
    {"name": "Rogue Holy Titan Pads Reb+3", "max_price": 100000000, "item_ids": ["0f48420f"]},
    {"name": "Rogue Holy Titan Pads Reb+4", "max_price": 220000000, "item_ids": ["1048420f"]},
    {"name": "Rogue Holy Titan Pads Reb+5", "max_price": 220000000, "item_ids": ["1148420f"]},
    {"name": "Rogue Holy Titan Pads Reb+6", "max_price": 500000000, "item_ids": ["1248420f"]},
    {"name": "Rogue Holy Titan Pads Reb+7", "max_price": 500000000, "item_ids": ["1348420f"]},
    {"name": "Rogue Holy Titan Pads Reb+8", "max_price": 1000000000, "item_ids": ["1448420f"]},
    {"name": "Rogue Holy Titan Pads Reb+9", "max_price": 1000000000, "item_ids": ["1548420f"]},
    {"name": "Rogue Holy Titan Pads Reb+10", "max_price": 5000000000, "item_ids": ["1648420f"]},
    {"name": "Rogue Holy Titan Pads Reb+11", "max_price": 5000000000, "item_ids": ["1748420f"]},
    {"name": "Rogue Holy Titan Pads Reb+12", "max_price": 5000000000, "item_ids": ["1848420f"]},
    {"name": "Rogue Holy Titan Pads Reb+13", "max_price": 5000000000, "item_ids": ["1948420f"]},
    {"name": "Rogue Holy Titan Pads Reb+14", "max_price": 5000000000, "item_ids": ["1a48420f"]},
    {"name": "Rogue Holy Titan Pads Reb+15", "max_price": 5000000000, "item_ids": ["1b48420f"]},
    {"name": "Rogue Holy Titan Pads Reb+16", "max_price": 5000000000, "item_ids": ["1c48420f"]},
    {"name": "Rogue Holy Titan Pads Reb+17", "max_price": 5000000000, "item_ids": ["1d48420f"]},
    {"name": "Rogue Holy Titan Pads Reb+18", "max_price": 5000000000, "item_ids": ["1e48420f"]},
    {"name": "Rogue Holy Titan Pads Reb+19", "max_price": 5000000000, "item_ids": ["1f48420f"]},
    {"name": "Rogue Holy Titan Pads Reb+20", "max_price": 5000000000, "item_ids": ["2048420f"]},
    {"name": "Rogue Holy Titan Pads Reb+21", "max_price": 5000000000, "item_ids": ["2148420f"]},
    {"name": "Rogue Holy Titan Boots +5", "max_price": 5000000, "item_ids": ["0bbfa90e", "0dbda90e"]},
    {"name": "Rogue Holy Titan Boots +6", "max_price": 10000000, "item_ids": ["0cbfa90e", "0ebda90e"]},
    {"name": "Rogue Holy Titan Boots +7", "max_price": 30000000, "item_ids": ["0dbfa90e", "0fbda90e"]},
    {"name": "Rogue Holy Titan Boots +8", "max_price": 220000000, "item_ids": ["0ebfa90e", "10bda90e"]},
    {"name": "Rogue Holy Titan Boots +9", "max_price": 5000000000, "item_ids": ["0fbfa90e", "11bda90e"]},
    {"name": "Rogue Holy Titan Boots +10", "max_price": 5000000000, "item_ids": ["10bfa90e", "12bda90e"]},
    {"name": "Rogue Holy Titan Boots Reb+1", "max_price": 30000000, "item_ids": ["c553420f"]},
    {"name": "Rogue Holy Titan Boots Reb+2", "max_price": 30000000, "item_ids": ["c653420f"]},
    {"name": "Rogue Holy Titan Boots Reb+3", "max_price": 100000000, "item_ids": ["c753420f"]},
    {"name": "Rogue Holy Titan Boots Reb+4", "max_price": 220000000, "item_ids": ["c853420f"]},
    {"name": "Rogue Holy Titan Boots Reb+5", "max_price": 220000000, "item_ids": ["c953420f"]},
    {"name": "Rogue Holy Titan Boots Reb+6", "max_price": 500000000, "item_ids": ["ca53420f"]},
    {"name": "Rogue Holy Titan Boots Reb+7", "max_price": 500000000, "item_ids": ["cb53420f"]},
    {"name": "Rogue Holy Titan Boots Reb+8", "max_price": 1000000000, "item_ids": ["cc53420f"]},
    {"name": "Rogue Holy Titan Boots Reb+9", "max_price": 1000000000, "item_ids": ["cd53420f"]},
    {"name": "Rogue Holy Titan Boots Reb+10", "max_price": 5000000000, "item_ids": ["ce53420f"]},
    {"name": "Rogue Holy Titan Boots Reb+11", "max_price": 5000000000, "item_ids": ["cf53420f"]},
    {"name": "Rogue Holy Titan Boots Reb+12", "max_price": 5000000000, "item_ids": ["d053420f"]},
    {"name": "Rogue Holy Titan Boots Reb+13", "max_price": 5000000000, "item_ids": ["d153420f"]},
    {"name": "Rogue Holy Titan Boots Reb+14", "max_price": 5000000000, "item_ids": ["d253420f"]},
    {"name": "Rogue Holy Titan Boots Reb+15", "max_price": 5000000000, "item_ids": ["d353420f"]},
    {"name": "Rogue Holy Titan Boots Reb+16", "max_price": 5000000000, "item_ids": ["d453420f"]},
    {"name": "Rogue Holy Titan Boots Reb+17", "max_price": 5000000000, "item_ids": ["d553420f"]},
    {"name": "Rogue Holy Titan Boots Reb+18", "max_price": 5000000000, "item_ids": ["d653420f"]},
    {"name": "Rogue Holy Titan Boots Reb+19", "max_price": 5000000000, "item_ids": ["d753420f"]},
    {"name": "Rogue Holy Titan Boots Reb+20", "max_price": 5000000000, "item_ids": ["d853420f"]},
    {"name": "Rogue Holy Titan Boots Reb+21", "max_price": 5000000000, "item_ids": ["d953420f"]},
    {"name": "Rogue Holy Titan Gauntlets +5", "max_price": 5000000, "item_ids": ["25b9a90e", "23bba90e"]},
    {"name": "Rogue Holy Titan Gauntlets +6", "max_price": 10000000, "item_ids": ["24bba90e", "26b9a90e"]},
    {"name": "Rogue Holy Titan Gauntlets +7", "max_price": 30000000, "item_ids": ["27b9a90e", "25bba90e"]},
    {"name": "Rogue Holy Titan Gauntlets +8", "max_price": 220000000, "item_ids": ["26bba90e", "28b9a90e"]},
    {"name": "Rogue Holy Titan Gauntlets +9", "max_price": 5000000000, "item_ids": ["29b9a90e", "27bba90e"]},
    {"name": "Rogue Holy Titan Gauntlets +10", "max_price": 5000000000, "item_ids": ["2ab9a90e", "28bba90e"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+1", "max_price": 30000000, "item_ids": ["dd4f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+2", "max_price": 30000000, "item_ids": ["de4f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+3", "max_price": 100000000, "item_ids": ["df4f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+4", "max_price": 220000000, "item_ids": ["e04f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+5", "max_price": 220000000, "item_ids": ["e14f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+6", "max_price": 500000000, "item_ids": ["e24f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+7", "max_price": 500000000, "item_ids": ["e34f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+8", "max_price": 1000000000, "item_ids": ["e44f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+9", "max_price": 1000000000, "item_ids": ["e54f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+10", "max_price": 5000000000, "item_ids": ["e64f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+11", "max_price": 5000000000, "item_ids": ["e74f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+12", "max_price": 5000000000, "item_ids": ["e84f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+13", "max_price": 5000000000, "item_ids": ["e94f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+14", "max_price": 5000000000, "item_ids": ["ea4f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+15", "max_price": 5000000000, "item_ids": ["eb4f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+16", "max_price": 5000000000, "item_ids": ["ec4f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+17", "max_price": 5000000000, "item_ids": ["ed4f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+18", "max_price": 5000000000, "item_ids": ["ee4f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+19", "max_price": 5000000000, "item_ids": ["ef4f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+20", "max_price": 5000000000, "item_ids": ["f04f420f"]},
    {"name": "Rogue Holy Titan Gauntlets Reb+21", "max_price": 5000000000, "item_ids": ["f14f420f"]},
    {"name": "Rogue Titan Helmet +5", "max_price": 5000000, "item_ids": ["fd729a0e", "fb749a0e"]},
    {"name": "Rogue Titan Helmet +6", "max_price": 3000000, "item_ids": ["fe729a0e", "fc749a0e"]},
    {"name": "Rogue Titan Helmet +7", "max_price": 10000000, "item_ids": ["fd749a0e", "ff729a0e"]},
    {"name": "Rogue Titan Helmet +8", "max_price": 220000000, "item_ids": ["00729a0e", "fe749a0e"]},
    {"name": "Rogue Titan Helmet +9", "max_price": 5000000000, "item_ids": ["ff749a0e", "01729a0e"]},
    {"name": "Rogue Titan Helmet +10", "max_price": 5000000000, "item_ids": ["00749a0e", "02729a0e"]},
    {"name": "Rogue Titan Helmet Reb+1", "max_price": 10000000, "item_ids": ["b509330f"]},
    {"name": "Rogue Titan Helmet Reb+2", "max_price": 10000000, "item_ids": ["b609330f"]},
    {"name": "Rogue Titan Helmet Reb+3", "max_price": 40000000, "item_ids": ["b709330f"]},
    {"name": "Rogue Titan Helmet Reb+4", "max_price": 40000000, "item_ids": ["b809330f"]},
    {"name": "Rogue Titan Helmet Reb+5", "max_price": 220000000, "item_ids": ["b909330f"]},
    {"name": "Rogue Titan Helmet Reb+6", "max_price": 500000000, "item_ids": ["ba09330f"]},
    {"name": "Rogue Titan Helmet Reb+7", "max_price": 500000000, "item_ids": ["bb09330f"]},
    {"name": "Rogue Titan Helmet Reb+8", "max_price": 500000000, "item_ids": ["bc09330f"]},
    {"name": "Rogue Titan Helmet Reb+9", "max_price": 1000000000, "item_ids": ["bd09330f"]},
    {"name": "Rogue Titan Helmet Reb+10", "max_price": 1000000000, "item_ids": ["be09330f"]},
    {"name": "Rogue Titan Helmet Reb+11", "max_price": 5000000000, "item_ids": ["bf09330f"]},
    {"name": "Rogue Titan Helmet Reb+12", "max_price": 5000000000, "item_ids": ["c009330f"]},
    {"name": "Rogue Titan Helmet Reb+13", "max_price": 5000000000, "item_ids": ["c109330f"]},
    {"name": "Rogue Titan Helmet Reb+14", "max_price": 5000000000, "item_ids": ["c209330f"]},
    {"name": "Rogue Titan Helmet Reb+15", "max_price": 5000000000, "item_ids": ["c309330f"]},
    {"name": "Rogue Titan Helmet Reb+16", "max_price": 5000000000, "item_ids": ["c409330f"]},
    {"name": "Rogue Titan Helmet Reb+17", "max_price": 5000000000, "item_ids": ["c509330f"]},
    {"name": "Rogue Titan Helmet Reb+18", "max_price": 5000000000, "item_ids": ["c609330f"]},
    {"name": "Rogue Titan Helmet Reb+19", "max_price": 5000000000, "item_ids": ["c709330f"]},
    {"name": "Rogue Titan Helmet Reb+20", "max_price": 5000000000, "item_ids": ["c809330f"]},
    {"name": "Rogue Titan Helmet Reb+21", "max_price": 5000000000, "item_ids": ["c909330f"]},
    {"name": "Rogue Titan Pauldron +6", "max_price": 3000000, "item_ids": ["2e6b9a0e", "2c6d9a0e"]},
    {"name": "Rogue Titan Pauldron +7", "max_price": 3000000, "item_ids": ["2f6b9a0e", "2d6d9a0e"]},
    {"name": "Rogue Titan Pauldron +8", "max_price": 220000000, "item_ids": ["306b9a0e", "2e6d9a0e"]},
    {"name": "Rogue Titan Pauldron +9", "max_price": 5000000000, "item_ids": ["316b9a0e", "2f6d9a0e"]},
    {"name": "Rogue Titan Pauldron +10", "max_price": 5000000000, "item_ids": ["326b9a0e", "306d9a0e"]},
    {"name": "Rogue Titan Pauldron Reb+1", "max_price": 10000000, "item_ids": ["e501330f"]},
    {"name": "Rogue Titan Pauldron Reb+2", "max_price": 10000000, "item_ids": ["e601330f"]},
    {"name": "Rogue Titan Pauldron Reb+3", "max_price": 40000000, "item_ids": ["e701330f"]},
    {"name": "Rogue Titan Pauldron Reb+4", "max_price": 40000000, "item_ids": ["e801330f"]},
    {"name": "Rogue Titan Pauldron Reb+5", "max_price": 220000000, "item_ids": ["e901330f"]},
    {"name": "Rogue Titan Pauldron Reb+6", "max_price": 500000000, "item_ids": ["ea01330f"]},
    {"name": "Rogue Titan Pauldron Reb+7", "max_price": 500000000, "item_ids": ["eb01330f"]},
    {"name": "Rogue Titan Pauldron Reb+8", "max_price": 500000000, "item_ids": ["ec01330f"]},
    {"name": "Rogue Titan Pauldron Reb+9", "max_price": 1000000000, "item_ids": ["ed01330f"]},
    {"name": "Rogue Titan Pauldron Reb+10", "max_price": 1000000000, "item_ids": ["ee01330f"]},
    {"name": "Rogue Titan Pauldron Reb+11", "max_price": 5000000000, "item_ids": ["ef01330f"]},
    {"name": "Rogue Titan Pauldron Reb+12", "max_price": 5000000000, "item_ids": ["f001330f"]},
    {"name": "Rogue Titan Pauldron Reb+13", "max_price": 5000000000, "item_ids": ["f101330f"]},
    {"name": "Rogue Titan Pauldron Reb+14", "max_price": 5000000000, "item_ids": ["f201330f"]},
    {"name": "Rogue Titan Pauldron Reb+15", "max_price": 5000000000, "item_ids": ["f301330f"]},
    {"name": "Rogue Titan Pauldron Reb+16", "max_price": 5000000000, "item_ids": ["f401330f"]},
    {"name": "Rogue Titan Pauldron Reb+17", "max_price": 5000000000, "item_ids": ["f501330f"]},
    {"name": "Rogue Titan Pauldron Reb+18", "max_price": 5000000000, "item_ids": ["f601330f"]},
    {"name": "Rogue Titan Pauldron Reb+19", "max_price": 5000000000, "item_ids": ["f701330f"]},
    {"name": "Rogue Titan Pauldron Reb+20", "max_price": 5000000000, "item_ids": ["f801330f"]},
    {"name": "Rogue Titan Pauldron Reb+21", "max_price": 5000000000, "item_ids": ["f901330f"]},
    {"name": "Rogue Titan Pads +6", "max_price": 3000000, "item_ids": ["166f9a0e", "14719a0e"]},
    {"name": "Rogue Titan Pads +7", "max_price": 10000000, "item_ids": ["15719a0e", "176f9a0e"]},
    {"name": "Rogue Titan Pads +8", "max_price": 220000000, "item_ids": ["186f9a0e", "16719a0e"]},
    {"name": "Rogue Titan Pads +9", "max_price": 5000000000, "item_ids": ["17719a0e", "196f9a0e"]},
    {"name": "Rogue Titan Pads +10", "max_price": 5000000000, "item_ids": ["18719a0e", "1a6f9a0e"]},
    {"name": "Rogue Titan Pads Reb+1", "max_price": 10000000, "item_ids": ["cd05330f"]},
    {"name": "Rogue Titan Pads Reb+2", "max_price": 10000000, "item_ids": ["ce05330f"]},
    {"name": "Rogue Titan Pads Reb+3", "max_price": 40000000, "item_ids": ["cf05330f"]},
    {"name": "Rogue Titan Pads Reb+4", "max_price": 40000000, "item_ids": ["d005330f"]},
    {"name": "Rogue Titan Pads Reb+5", "max_price": 220000000, "item_ids": ["d105330f"]},
    {"name": "Rogue Titan Pads Reb+6", "max_price": 500000000, "item_ids": ["d205330f"]},
    {"name": "Rogue Titan Pads Reb+7", "max_price": 500000000, "item_ids": ["d305330f"]},
    {"name": "Rogue Titan Pads Reb+8", "max_price": 500000000, "item_ids": ["d405330f"]},
    {"name": "Rogue Titan Pads Reb+9", "max_price": 1000000000, "item_ids": ["d505330f"]},
    {"name": "Rogue Titan Pads Reb+10", "max_price": 1000000000, "item_ids": ["d605330f"]},
    {"name": "Rogue Titan Pads Reb+11", "max_price": 5000000000, "item_ids": ["d705330f"]},
    {"name": "Rogue Titan Pads Reb+12", "max_price": 5000000000, "item_ids": ["d805330f"]},
    {"name": "Rogue Titan Pads Reb+13", "max_price": 5000000000, "item_ids": ["d905330f"]},
    {"name": "Rogue Titan Pads Reb+14", "max_price": 5000000000, "item_ids": ["da05330f"]},
    {"name": "Rogue Titan Pads Reb+15", "max_price": 5000000000, "item_ids": ["db05330f"]},
    {"name": "Rogue Titan Pads Reb+16", "max_price": 5000000000, "item_ids": ["dc05330f"]},
    {"name": "Rogue Titan Pads Reb+17", "max_price": 5000000000, "item_ids": ["dd05330f"]},
    {"name": "Rogue Titan Pads Reb+18", "max_price": 5000000000, "item_ids": ["de05330f"]},
    {"name": "Rogue Titan Pads Reb+19", "max_price": 5000000000, "item_ids": ["df05330f"]},
    {"name": "Rogue Titan Pads Reb+20", "max_price": 5000000000, "item_ids": ["e005330f"]},
    {"name": "Rogue Titan Pads Reb+21", "max_price": 5000000000, "item_ids": ["e105330f"]},
    {"name": "Rogue Titan Boots +6", "max_price": 3000000, "item_ids": ["ce7a9a0e", "cc7c9a0e"]},
    {"name": "Rogue Titan Boots +7", "max_price": 10000000, "item_ids": ["cf7a9a0e", "cd7c9a0e"]},
    {"name": "Rogue Titan Boots +8", "max_price": 220000000, "item_ids": ["ce7c9a0e", "d07a9a0e"]},
    {"name": "Rogue Titan Boots +9", "max_price": 5000000000, "item_ids": ["cf7c9a0e", "d17a9a0e"]},
    {"name": "Rogue Titan Boots +10", "max_price": 5000000000, "item_ids": ["d07c9a0e", "d27a9a0e"]},
    {"name": "Rogue Titan Boots Reb+1", "max_price": 10000000, "item_ids": ["8511330f"]},
    {"name": "Rogue Titan Boots Reb+2", "max_price": 10000000, "item_ids": ["8611330f"]},
    {"name": "Rogue Titan Boots Reb+3", "max_price": 40000000, "item_ids": ["8711330f"]},
    {"name": "Rogue Titan Boots Reb+4", "max_price": 40000000, "item_ids": ["8811330f"]},
    {"name": "Rogue Titan Boots Reb+5", "max_price": 220000000, "item_ids": ["8911330f"]},
    {"name": "Rogue Titan Boots Reb+6", "max_price": 500000000, "item_ids": ["8a11330f"]},
    {"name": "Rogue Titan Boots Reb+7", "max_price": 500000000, "item_ids": ["8b11330f"]},
    {"name": "Rogue Titan Boots Reb+8", "max_price": 500000000, "item_ids": ["8c11330f"]},
    {"name": "Rogue Titan Boots Reb+9", "max_price": 1000000000, "item_ids": ["8d11330f"]},
    {"name": "Rogue Titan Boots Reb+10", "max_price": 1000000000, "item_ids": ["8e11330f"]},
    {"name": "Rogue Titan Boots Reb+11", "max_price": 5000000000, "item_ids": ["8f11330f"]},
    {"name": "Rogue Titan Boots Reb+12", "max_price": 5000000000, "item_ids": ["9011330f"]},
    {"name": "Rogue Titan Boots Reb+13", "max_price": 5000000000, "item_ids": ["9111330f"]},
    {"name": "Rogue Titan Boots Reb+14", "max_price": 5000000000, "item_ids": ["9211330f"]},
    {"name": "Rogue Titan Boots Reb+15", "max_price": 5000000000, "item_ids": ["9311330f"]},
    {"name": "Rogue Titan Boots Reb+16", "max_price": 5000000000, "item_ids": ["9411330f"]},
    {"name": "Rogue Titan Boots Reb+17", "max_price": 5000000000, "item_ids": ["9511330f"]},
    {"name": "Rogue Titan Boots Reb+18", "max_price": 5000000000, "item_ids": ["9611330f"]},
    {"name": "Rogue Titan Boots Reb+19", "max_price": 5000000000, "item_ids": ["9711330f"]},
    {"name": "Rogue Titan Boots Reb+20", "max_price": 5000000000, "item_ids": ["9811330f"]},
    {"name": "Rogue Titan Boots Reb+21", "max_price": 5000000000, "item_ids": ["9911330f"]},
    {"name": "Rogue Titan Gauntlets +6", "max_price": 3000000, "item_ids": ["e6769a0e", "e4789a0e"]},
    {"name": "Rogue Titan Gauntlets +7", "max_price": 10000000, "item_ids": ["e7769a0e", "e5789a0e"]},
    {"name": "Rogue Titan Gauntlets +8", "max_price": 220000000, "item_ids": ["e8769a0e", "e6789a0e"]},
    {"name": "Rogue Titan Gauntlets +9", "max_price": 5000000000, "item_ids": ["e9769a0e", "e7789a0e"]},
    {"name": "Rogue Titan Gauntlets +10", "max_price": 5000000000, "item_ids": ["ea769a0e", "e8789a0e"]},
    {"name": "Rogue Titan Gauntlets Reb+1", "max_price": 10000000, "item_ids": ["9d0d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+2", "max_price": 10000000, "item_ids": ["9e0d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+3", "max_price": 40000000, "item_ids": ["9f0d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+4", "max_price": 40000000, "item_ids": ["a00d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+5", "max_price": 220000000, "item_ids": ["a10d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+6", "max_price": 500000000, "item_ids": ["a20d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+7", "max_price": 500000000, "item_ids": ["a30d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+8", "max_price": 500000000, "item_ids": ["a40d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+9", "max_price": 1000000000, "item_ids": ["a50d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+10", "max_price": 1000000000, "item_ids": ["a60d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+11", "max_price": 5000000000, "item_ids": ["a70d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+12", "max_price": 5000000000, "item_ids": ["a80d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+13", "max_price": 5000000000, "item_ids": ["a90d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+14", "max_price": 5000000000, "item_ids": ["aa0d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+15", "max_price": 5000000000, "item_ids": ["ab0d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+16", "max_price": 5000000000, "item_ids": ["ac0d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+17", "max_price": 5000000000, "item_ids": ["ad0d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+18", "max_price": 5000000000, "item_ids": ["ae0d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+19", "max_price": 5000000000, "item_ids": ["af0d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+20", "max_price": 5000000000, "item_ids": ["b00d330f"]},
    {"name": "Rogue Titan Gauntlets Reb+21", "max_price": 5000000000, "item_ids": ["b10d330f"]},
    {"name": "Rogue Full Guard Helmet +7", "max_price": 3000000, "item_ids": ["bf308b0e", "bd328b0e"]},
    {"name": "Rogue Full Guard Helmet +8", "max_price": 30000000, "item_ids": ["be328b0e", "c0308b0e"]},
    {"name": "Rogue Full Guard Helmet +9", "max_price": 220000000, "item_ids": ["bf328b0e", "c1308b0e"]},
    {"name": "Rogue Full Guard Helmet +10", "max_price": 5000000000, "item_ids": ["c0328b0e", "c2308b0e"]},
    {"name": "Rogue Full Guard Pauldron +7", "max_price": 3000000, "item_ids": ["ed2a8b0e", "ef288b0e"]},
    {"name": "Rogue Full Guard Pauldron +8", "max_price": 30000000, "item_ids": ["ee2a8b0e", "f0288b0e"]},
    {"name": "Rogue Full Guard Pauldron +9", "max_price": 220000000, "item_ids": ["ef2a8b0e", "f1288b0e"]},
    {"name": "Rogue Full Guard Pauldron +10", "max_price": 5000000000, "item_ids": ["f02a8b0e", "f2288b0e"]},
    {"name": "Rogue Full Guard Pads +7", "max_price": 3000000, "item_ids": ["d72c8b0e", "d52e8b0e"]},
    {"name": "Rogue Full Guard Pads +8", "max_price": 30000000, "item_ids": ["d62e8b0e", "d82c8b0e"]},
    {"name": "Rogue Full Guard Pads +9", "max_price": 220000000, "item_ids": ["d72e8b0e", "d92c8b0e"]},
    {"name": "Rogue Full Guard Pads +10", "max_price": 5000000000, "item_ids": ["d82e8b0e", "da2c8b0e"]},
    {"name": "Rogue Full Guard Boots +7", "max_price": 3000000, "item_ids": ["8f388b0e", "8d3a8b0e"]},
    {"name": "Rogue Full Guard Boots +8", "max_price": 30000000, "item_ids": ["90388b0e", "8e3a8b0e"]},
    {"name": "Rogue Full Guard Boots +9", "max_price": 220000000, "item_ids": ["91388b0e", "8f3a8b0e"]},
    {"name": "Rogue Full Guard Boots +10", "max_price": 5000000000, "item_ids": ["92388b0e", "903a8b0e"]},
    {"name": "Rogue Full Guard Gauntlets +7", "max_price": 3000000, "item_ids": ["a5368b0e", "a7348b0e"]},
    {"name": "Rogue Full Guard Gauntlets +8", "max_price": 30000000, "item_ids": ["a6368b0e", "a8348b0e"]},
    {"name": "Rogue Full Guard Gauntlets +9", "max_price": 220000000, "item_ids": ["a7368b0e", "a9348b0e"]},
    {"name": "Rogue Full Guard Gauntlets +10", "max_price": 5000000000, "item_ids": ["a8368b0e", "aa348b0e"]},
    {"name": "Rogue Elder Armor Boots +5", "max_price": 100000000, "item_ids": ["4da29a20", "4ba49a20"]},
    {"name": "Rogue Elder Armor Boots +6", "max_price": 100000000, "item_ids": ["4ea29a20", "4ca49a20"]},
    {"name": "Rogue Elder Armor Boots +7", "max_price": 220000000, "item_ids": ["4da49a20", "4fa29a20"]},
    {"name": "Rogue Elder Armor Boots +8", "max_price": 220000000, "item_ids": ["50a29a20", "4ea49a20"]},
    {"name": "Rogue Elder Armor Helmet +5", "max_price": 100000000, "item_ids": ["7d9a9a20", "7b9c9a20"]},
    {"name": "Rogue Elder Armor Helmet +6", "max_price": 100000000, "item_ids": ["7e9a9a20", "7c9c9a20"]},
    {"name": "Rogue Elder Armor Helmet +7", "max_price": 220000000, "item_ids": ["7d9c9a20", "7f9a9a20"]},
    {"name": "Rogue Elder Armor Helmet +8", "max_price": 220000000, "item_ids": ["809a9a20", "7e9c9a20"]},
    {"name": "Rogue Elder Armor Pauldron +5", "max_price": 100000000, "item_ids": ["ad929a20", "ab949a20"]},
    {"name": "Rogue Elder Armor Pauldron +6", "max_price": 100000000, "item_ids": ["ae929a20", "ac949a20"]},
    {"name": "Rogue Elder Armor Pauldron +7", "max_price": 220000000, "item_ids": ["af929a20", "ad949a20"]},
    {"name": "Rogue Elder Armor Pauldron +8", "max_price": 1000000000, "item_ids": ["b0929a20", "ae949a20"]},
    {"name": "Rogue Elder Armor Pauldron Reb+1", "max_price": 220000000, "item_ids": ["65293321"]},
    {"name": "Rogue Elder Armor Pauldron Reb+2", "max_price": 400000000, "item_ids": ["66293321"]},
    {"name": "Rogue Elder Armor Pauldron Reb+3", "max_price": 600000000, "item_ids": ["67293321"]},
    {"name": "Rogue Elder Armor Pauldron Reb+4", "max_price": 1000000000, "item_ids": ["68293321"]},
    {"name": "Rogue Elder Armor Pauldron Reb+5", "max_price": 1000000000, "item_ids": ["69293321"]},
    {"name": "Rogue Elder Armor Gauntlets +5", "max_price": 100000000, "item_ids": ["659e9a20", "63a09a20"]},
    {"name": "Rogue Elder Armor Gauntlets +6", "max_price": 100000000, "item_ids": ["669e9a20", "64a09a20"]},
    {"name": "Rogue Elder Armor Gauntlets +7", "max_price": 220000000, "item_ids": ["65a09a20", "679e9a20"]},
    {"name": "Rogue Elder Armor Gauntlets +8", "max_price": 220000000, "item_ids": ["689e9a20", "66a09a20"]},
    {"name": "Rogue Elder Armor Pads +5", "max_price": 100000000, "item_ids": ["95969a20", "93989a20"]},
    {"name": "Rogue Elder Armor Pads +6", "max_price": 100000000, "item_ids": ["96969a20", "94989a20"]},
    {"name": "Rogue Elder Armor Pads +7", "max_price": 220000000, "item_ids": ["97969a20", "95989a20"]},
    {"name": "Rogue Elder Armor Pads +8", "max_price": 220000000, "item_ids": ["98969a20", "96989a20"]},
    {"name": "Priest Holy Titan Helmet +5", "max_price": 5000000, "item_ids": ["31110c11"]},
    {"name": "Priest Holy Titan Helmet +6", "max_price": 10000000, "item_ids": ["32110c11"]},
    {"name": "Priest Holy Titan Helmet +7", "max_price": 30000000, "item_ids": ["33110c11"]},
    {"name": "Priest Holy Titan Helmet +8", "max_price": 220000000, "item_ids": ["34110c11"]},
    {"name": "Priest Holy Titan Helmet +9", "max_price": 5000000000, "item_ids": ["35110c11"]},
    {"name": "Priest Holy Titan Helmet +10", "max_price": 5000000000, "item_ids": ["36110c11"]},
    {"name": "Priest Holy Titan Helmet Reb+1", "max_price": 30000000, "item_ids": ["d7a5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+2", "max_price": 30000000, "item_ids": ["d8a5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+3", "max_price": 100000000, "item_ids": ["d9a5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+4", "max_price": 220000000, "item_ids": ["daa5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+5", "max_price": 220000000, "item_ids": ["dba5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+6", "max_price": 400000000, "item_ids": ["dca5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+7", "max_price": 400000000, "item_ids": ["dda5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+8", "max_price": 800000000, "item_ids": ["dea5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+9", "max_price": 1250000000, "item_ids": ["dfa5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+10", "max_price": 2000000000, "item_ids": ["e0a5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+11", "max_price": 5000000000, "item_ids": ["e1a5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+12", "max_price": 5000000000, "item_ids": ["e2a5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+13", "max_price": 5000000000, "item_ids": ["e3a5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+14", "max_price": 5000000000, "item_ids": ["e4a5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+15", "max_price": 5000000000, "item_ids": ["e5a5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+16", "max_price": 5000000000, "item_ids": ["e6a5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+17", "max_price": 5000000000, "item_ids": ["e7a5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+18", "max_price": 5000000000, "item_ids": ["e8a5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+19", "max_price": 5000000000, "item_ids": ["e9a5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+20", "max_price": 5000000000, "item_ids": ["eaa5a411"]},
    {"name": "Priest Holy Titan Helmet Reb+21", "max_price": 5000000000, "item_ids": ["eba5a411"]},
    {"name": "Priest Holy Titan Pauldron +5", "max_price": 5000000, "item_ids": ["6d070c11", "61090c11"]},
    {"name": "Priest Holy Titan Pauldron +6", "max_price": 10000000, "item_ids": ["6e070c11", "62090c11"]},
    {"name": "Priest Holy Titan Pauldron +7", "max_price": 30000000, "item_ids": ["63090c11", "6f070c11"]},
    {"name": "Priest Holy Titan Pauldron +8", "max_price": 220000000, "item_ids": ["70070c11", "64090c11"]},
    {"name": "Priest Holy Titan Pauldron +9", "max_price": 5000000000, "item_ids": ["65090c11", "71070c11"]},
    {"name": "Priest Holy Titan Pauldron +10", "max_price": 5000000000, "item_ids": ["66090c11", "72070c11"]},
    {"name": "Priest Holy Titan Pauldron Reb+1", "max_price": 30000000, "item_ids": ["079ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+2", "max_price": 30000000, "item_ids": ["089ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+3", "max_price": 100000000, "item_ids": ["099ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+4", "max_price": 220000000, "item_ids": ["0a9ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+5", "max_price": 220000000, "item_ids": ["0b9ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+6", "max_price": 400000000, "item_ids": ["0c9ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+7", "max_price": 400000000, "item_ids": ["0d9ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+8", "max_price": 800000000, "item_ids": ["0e9ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+9", "max_price": 1250000000, "item_ids": ["0f9ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+10", "max_price": 2000000000, "item_ids": ["109ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+11", "max_price": 5000000000, "item_ids": ["119ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+12", "max_price": 5000000000, "item_ids": ["129ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+13", "max_price": 5000000000, "item_ids": ["139ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+14", "max_price": 5000000000, "item_ids": ["149ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+15", "max_price": 5000000000, "item_ids": ["159ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+16", "max_price": 5000000000, "item_ids": ["169ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+17", "max_price": 5000000000, "item_ids": ["179ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+18", "max_price": 5000000000, "item_ids": ["189ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+19", "max_price": 5000000000, "item_ids": ["199ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+20", "max_price": 5000000000, "item_ids": ["1a9ea411"]},
    {"name": "Priest Holy Titan Pauldron Reb+21", "max_price": 5000000000, "item_ids": ["1b9ea411"]},
    {"name": "Priest Holy Titan Pads +5", "max_price": 5000000, "item_ids": ["550b0c11", "490d0c11"]},
    {"name": "Priest Holy Titan Pads +6", "max_price": 10000000, "item_ids": ["560b0c11", "4a0d0c11"]},
    {"name": "Priest Holy Titan Pads +7", "max_price": 30000000, "item_ids": ["570b0c11", "4b0d0c11"]},
    {"name": "Priest Holy Titan Pads +8", "max_price": 220000000, "item_ids": ["580b0c11", "4c0d0c11"]},
    {"name": "Priest Holy Titan Pads +9", "max_price": 5000000000, "item_ids": ["590b0c11", "4d0d0c11"]},
    {"name": "Priest Holy Titan Pads +10", "max_price": 5000000000, "item_ids": ["5a0b0c11", "4e0d0c11"]},
    {"name": "Priest Holy Titan Pads Reb+1", "max_price": 30000000, "item_ids": ["efa1a411"]},
    {"name": "Priest Holy Titan Pads Reb+2", "max_price": 30000000, "item_ids": ["f0a1a411"]},
    {"name": "Priest Holy Titan Pads Reb+3", "max_price": 100000000, "item_ids": ["f1a1a411"]},
    {"name": "Priest Holy Titan Pads Reb+4", "max_price": 220000000, "item_ids": ["f2a1a411"]},
    {"name": "Priest Holy Titan Pads Reb+5", "max_price": 220000000, "item_ids": ["f3a1a411"]},
    {"name": "Priest Holy Titan Pads Reb+6", "max_price": 400000000, "item_ids": ["f4a1a411"]},
    {"name": "Priest Holy Titan Pads Reb+7", "max_price": 400000000, "item_ids": ["f5a1a411"]},
    {"name": "Priest Holy Titan Pads Reb+8", "max_price": 800000000, "item_ids": ["f6a1a411"]},
    {"name": "Priest Holy Titan Pads Reb+9", "max_price": 1250000000, "item_ids": ["f7a1a411"]},
    {"name": "Priest Holy Titan Pads Reb+10", "max_price": 2000000000, "item_ids": ["f8a1a411"]},
    {"name": "Priest Holy Titan Pads Reb+11", "max_price": 5000000000, "item_ids": ["f9a1a411"]},
    {"name": "Priest Holy Titan Pads Reb+12", "max_price": 5000000000, "item_ids": ["faa1a411"]},
    {"name": "Priest Holy Titan Pads Reb+13", "max_price": 5000000000, "item_ids": ["fba1a411"]},
    {"name": "Priest Holy Titan Pads Reb+14", "max_price": 5000000000, "item_ids": ["fca1a411"]},
    {"name": "Priest Holy Titan Pads Reb+15", "max_price": 5000000000, "item_ids": ["fda1a411"]},
    {"name": "Priest Holy Titan Pads Reb+16", "max_price": 5000000000, "item_ids": ["fea1a411"]},
    {"name": "Priest Holy Titan Pads Reb+17", "max_price": 5000000000, "item_ids": ["ffa1a411"]},
    {"name": "Priest Holy Titan Pads Reb+18", "max_price": 5000000000, "item_ids": ["00a1a411"]},
    {"name": "Priest Holy Titan Pads Reb+19", "max_price": 5000000000, "item_ids": ["01a1a411"]},
    {"name": "Priest Holy Titan Pads Reb+20", "max_price": 5000000000, "item_ids": ["02a1a411"]},
    {"name": "Priest Holy Titan Pads Reb+21", "max_price": 5000000000, "item_ids": ["03a1a411"]},
    {"name": "Priest Holy Titan Boots +5", "max_price": 5000000, "item_ids": ["01190c11", "3d0f0c11"]},
    {"name": "Priest Holy Titan Boots +6", "max_price": 10000000, "item_ids": ["3e0f0c11", "02190c11"]},
    {"name": "Priest Holy Titan Boots +7", "max_price": 30000000, "item_ids": ["03190c11", "3f0f0c11"]},
    {"name": "Priest Holy Titan Boots +8", "max_price": 220000000, "item_ids": ["04190c11", "400f0c11"]},
    {"name": "Priest Holy Titan Boots +9", "max_price": 5000000000, "item_ids": ["05190c11", "410f0c11"]},
    {"name": "Priest Holy Titan Boots +10", "max_price": 5000000000, "item_ids": ["06190c11", "420f0c11"]},
    {"name": "Priest Holy Titan Boots Reb+1", "max_price": 30000000, "item_ids": ["a7ada411"]},
    {"name": "Priest Holy Titan Boots Reb+2", "max_price": 30000000, "item_ids": ["a8ada411"]},
    {"name": "Priest Holy Titan Boots Reb+3", "max_price": 100000000, "item_ids": ["a9ada411"]},
    {"name": "Priest Holy Titan Boots Reb+4", "max_price": 220000000, "item_ids": ["aaada411"]},
    {"name": "Priest Holy Titan Boots Reb+5", "max_price": 220000000, "item_ids": ["abada411"]},
    {"name": "Priest Holy Titan Boots Reb+6", "max_price": 400000000, "item_ids": ["acada411"]},
    {"name": "Priest Holy Titan Boots Reb+7", "max_price": 400000000, "item_ids": ["adada411"]},
    {"name": "Priest Holy Titan Boots Reb+8", "max_price": 800000000, "item_ids": ["aeada411"]},
    {"name": "Priest Holy Titan Boots Reb+9", "max_price": 1250000000, "item_ids": ["afada411"]},
    {"name": "Priest Holy Titan Boots Reb+10", "max_price": 2000000000, "item_ids": ["b0ada411"]},
    {"name": "Priest Holy Titan Boots Reb+11", "max_price": 5000000000, "item_ids": ["b1ada411"]},
    {"name": "Priest Holy Titan Boots Reb+12", "max_price": 5000000000, "item_ids": ["b2ada411"]},
    {"name": "Priest Holy Titan Boots Reb+13", "max_price": 5000000000, "item_ids": ["b3ada411"]},
    {"name": "Priest Holy Titan Boots Reb+14", "max_price": 5000000000, "item_ids": ["b4ada411"]},
    {"name": "Priest Holy Titan Boots Reb+15", "max_price": 5000000000, "item_ids": ["b5ada411"]},
    {"name": "Priest Holy Titan Boots Reb+16", "max_price": 5000000000, "item_ids": ["b6ada411"]},
    {"name": "Priest Holy Titan Boots Reb+17", "max_price": 5000000000, "item_ids": ["b7ada411"]},
    {"name": "Priest Holy Titan Boots Reb+18", "max_price": 5000000000, "item_ids": ["b8ada411"]},
    {"name": "Priest Holy Titan Boots Reb+19", "max_price": 5000000000, "item_ids": ["b9ada411"]},
    {"name": "Priest Holy Titan Boots Reb+20", "max_price": 5000000000, "item_ids": ["baada411"]},
    {"name": "Priest Holy Titan Boots Reb+21", "max_price": 5000000000, "item_ids": ["bbada411"]},
    {"name": "Priest Holy Titan Gauntlets +5", "max_price": 5000000, "item_ids": ["25130c11"]},
    {"name": "Priest Holy Titan Gauntlets +6", "max_price": 10000000, "item_ids": ["26130c11"]},
    {"name": "Priest Holy Titan Gauntlets +7", "max_price": 30000000, "item_ids": ["27130c11"]},
    {"name": "Priest Holy Titan Gauntlets +8", "max_price": 220000000, "item_ids": ["28130c11"]},
    {"name": "Priest Holy Titan Gauntlets +9", "max_price": 5000000000, "item_ids": ["29130c11"]},
    {"name": "Priest Holy Titan Gauntlets +10", "max_price": 5000000000, "item_ids": ["2a130c11"]},
    {"name": "Priest Holy Titan Gauntlets Reb+1", "max_price": 30000000, "item_ids": ["bfa9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+2", "max_price": 30000000, "item_ids": ["c0a9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+3", "max_price": 100000000, "item_ids": ["c1a9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+4", "max_price": 220000000, "item_ids": ["c2a9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+5", "max_price": 220000000, "item_ids": ["c3a9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+6", "max_price": 400000000, "item_ids": ["c4a9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+7", "max_price": 400000000, "item_ids": ["c5a9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+8", "max_price": 800000000, "item_ids": ["c6a9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+9", "max_price": 1250000000, "item_ids": ["c7a9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+10", "max_price": 2000000000, "item_ids": ["c8a9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+11", "max_price": 5000000000, "item_ids": ["c9a9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+12", "max_price": 5000000000, "item_ids": ["caa9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+13", "max_price": 5000000000, "item_ids": ["cba9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+14", "max_price": 5000000000, "item_ids": ["cca9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+15", "max_price": 5000000000, "item_ids": ["cda9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+16", "max_price": 5000000000, "item_ids": ["cea9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+17", "max_price": 5000000000, "item_ids": ["cfa9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+18", "max_price": 5000000000, "item_ids": ["d0a9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+19", "max_price": 5000000000, "item_ids": ["d1a9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+20", "max_price": 5000000000, "item_ids": ["d2a9a411"]},
    {"name": "Priest Holy Titan Gauntlets Reb+21", "max_price": 5000000000, "item_ids": ["d3a9a411"]},
    {"name": "Priest Titan Helmet +7", "max_price": 10000000, "item_ids": ["ffccfc10", "f3cefc10"]},
    {"name": "Priest Titan Helmet +8", "max_price": 220000000, "item_ids": ["f4cefc10", "00ccfc10"]},
    {"name": "Priest Titan Helmet +9", "max_price": 2000000000, "item_ids": ["f5cefc10", "01ccfc10"]},
    {"name": "Priest Titan Helmet +10", "max_price": 5000000000, "item_ids": ["f6cefc10", "02ccfc10"]},
    {"name": "Priest Titan Helmet Reb+1", "max_price": 10000000, "item_ids": ["97639511"]},
    {"name": "Priest Titan Helmet Reb+2", "max_price": 10000000, "item_ids": ["98639511"]},
    {"name": "Priest Titan Helmet Reb+3", "max_price": 40000000, "item_ids": ["99639511"]},
    {"name": "Priest Titan Helmet Reb+4", "max_price": 40000000, "item_ids": ["9a639511"]},
    {"name": "Priest Titan Helmet Reb+5", "max_price": 220000000, "item_ids": ["9b639511"]},
    {"name": "Priest Titan Helmet Reb+6", "max_price": 250000000, "item_ids": ["9c639511"]},
    {"name": "Priest Titan Helmet Reb+7", "max_price": 250000000, "item_ids": ["9d639511"]},
    {"name": "Priest Titan Helmet Reb+8", "max_price": 250000000, "item_ids": ["9e639511"]},
    {"name": "Priest Titan Helmet Reb+9", "max_price": 750000000, "item_ids": ["9f639511"]},
    {"name": "Priest Titan Helmet Reb+10", "max_price": 750000000, "item_ids": ["a0639511"]},
    {"name": "Priest Titan Helmet Reb+13", "max_price": 4000000000, "item_ids": ["a3639511"]},
    {"name": "Priest Titan Helmet Reb+14", "max_price": 5000000000, "item_ids": ["a4639511"]},
    {"name": "Priest Titan Helmet Reb+15", "max_price": 5000000000, "item_ids": ["a5639511"]},
    {"name": "Priest Titan Helmet Reb+16", "max_price": 5000000000, "item_ids": ["a6639511"]},
    {"name": "Priest Titan Helmet Reb+17", "max_price": 5000000000, "item_ids": ["a7639511"]},
    {"name": "Priest Titan Helmet Reb+18", "max_price": 5000000000, "item_ids": ["a8639511"]},
    {"name": "Priest Titan Helmet Reb+19", "max_price": 5000000000, "item_ids": ["a9639511"]},
    {"name": "Priest Titan Helmet Reb+20", "max_price": 5000000000, "item_ids": ["aa639511"]},
    {"name": "Priest Titan Helmet Reb+21", "max_price": 5000000000, "item_ids": ["ab639511"]},
    {"name": "Priest Titan Pauldron +6", "max_price": 3000000, "item_ids": ["2ec5fc10"]},
    {"name": "Priest Titan Pauldron +7", "max_price": 10000000, "item_ids": ["2fc5fc10"]},
    {"name": "Priest Titan Pauldron +8", "max_price": 220000000, "item_ids": ["30c5fc10"]},
    {"name": "Priest Titan Pauldron +9", "max_price": 2000000000, "item_ids": ["31c5fc10"]},
    {"name": "Priest Titan Pauldron +10", "max_price": 5000000000, "item_ids": ["32c5fc10"]},
    {"name": "Priest Titan Pads +6", "max_price": 3000000, "item_ids": ["16c9fc10", "0acbfc10"]},
    {"name": "Priest Titan Pads +7", "max_price": 10000000, "item_ids": ["17c9fc10", "0bcbfc10"]},
    {"name": "Priest Titan Pads +8", "max_price": 220000000, "item_ids": ["18c9fc10", "0ccbfc10"]},
    {"name": "Priest Titan Pads +10", "max_price": 5000000000, "item_ids": ["1ac9fc10", "0ecbfc10"]},
    {"name": "Priest Titan Pads Reb+1", "max_price": 10000000, "item_ids": ["af5f9511"]},
    {"name": "Priest Titan Pads Reb+2", "max_price": 10000000, "item_ids": ["b05f9511"]},
    {"name": "Priest Titan Pads Reb+3", "max_price": 40000000, "item_ids": ["b15f9511"]},
    {"name": "Priest Titan Pads Reb+4", "max_price": 40000000, "item_ids": ["b25f9511"]},
    {"name": "Priest Titan Pads Reb+5", "max_price": 220000000, "item_ids": ["b35f9511"]},
    {"name": "Priest Titan Pads Reb+6", "max_price": 250000000, "item_ids": ["b45f9511"]},
    {"name": "Priest Titan Pads Reb+7", "max_price": 250000000, "item_ids": ["b55f9511"]},
    {"name": "Priest Titan Pads Reb+8", "max_price": 250000000, "item_ids": ["b65f9511"]},
    {"name": "Priest Titan Pads Reb+9", "max_price": 750000000, "item_ids": ["b75f9511"]},
    {"name": "Priest Titan Pads Reb+10", "max_price": 750000000, "item_ids": ["b85f9511"]},
    {"name": "Priest Titan Pads Reb+13", "max_price": 4000000000, "item_ids": ["bb5f9511"]},
    {"name": "Priest Titan Pads Reb+14", "max_price": 5000000000, "item_ids": ["bc5f9511"]},
    {"name": "Priest Titan Pads Reb+15", "max_price": 5000000000, "item_ids": ["bd5f9511"]},
    {"name": "Priest Titan Pads Reb+16", "max_price": 5000000000, "item_ids": ["be5f9511"]},
    {"name": "Priest Titan Pads Reb+17", "max_price": 5000000000, "item_ids": ["bf5f9511"]},
    {"name": "Priest Titan Pads Reb+18", "max_price": 5000000000, "item_ids": ["c05f9511"]},
    {"name": "Priest Titan Pads Reb+19", "max_price": 5000000000, "item_ids": ["c15f9511"]},
    {"name": "Priest Titan Pads Reb+20", "max_price": 5000000000, "item_ids": ["c25f9511"]},
    {"name": "Priest Titan Pads Reb+21", "max_price": 5000000000, "item_ids": ["c35f9511"]},
    {"name": "Priest Titan Boots +6", "max_price": 3000000, "item_ids": ["c2d6fc10"]},
    {"name": "Priest Titan Boots +7", "max_price": 10000000, "item_ids": ["c3d6fc10"]},
    {"name": "Priest Titan Boots +8", "max_price": 220000000, "item_ids": ["c4d6fc10"]},
    {"name": "Priest Titan Boots +10", "max_price": 5000000000, "item_ids": ["c6d6fc10"]},
    {"name": "Priest Titan Boots Reb+1", "max_price": 10000000, "item_ids": ["676b9511"]},
    {"name": "Priest Titan Boots Reb+2", "max_price": 10000000, "item_ids": ["686b9511"]},
    {"name": "Priest Titan Boots Reb+3", "max_price": 40000000, "item_ids": ["696b9511"]},
    {"name": "Priest Titan Boots Reb+4", "max_price": 40000000, "item_ids": ["6a6b9511"]},
    {"name": "Priest Titan Boots Reb+5", "max_price": 220000000, "item_ids": ["6b6b9511"]},
    {"name": "Priest Titan Boots Reb+6", "max_price": 250000000, "item_ids": ["6c6b9511"]},
    {"name": "Priest Titan Boots Reb+7", "max_price": 250000000, "item_ids": ["6d6b9511"]},
    {"name": "Priest Titan Boots Reb+8", "max_price": 250000000, "item_ids": ["6e6b9511"]},
    {"name": "Priest Titan Boots Reb+9", "max_price": 750000000, "item_ids": ["6f6b9511"]},
    {"name": "Priest Titan Boots Reb+10", "max_price": 750000000, "item_ids": ["706b9511"]},
    {"name": "Priest Titan Boots Reb+13", "max_price": 4000000000, "item_ids": ["736b9511"]},
    {"name": "Priest Titan Boots Reb+14", "max_price": 5000000000, "item_ids": ["746b9511"]},
    {"name": "Priest Titan Boots Reb+15", "max_price": 5000000000, "item_ids": ["756b9511"]},
    {"name": "Priest Titan Boots Reb+16", "max_price": 5000000000, "item_ids": ["766b9511"]},
    {"name": "Priest Titan Boots Reb+17", "max_price": 5000000000, "item_ids": ["776b9511"]},
    {"name": "Priest Titan Boots Reb+18", "max_price": 5000000000, "item_ids": ["786b9511"]},
    {"name": "Priest Titan Boots Reb+19", "max_price": 5000000000, "item_ids": ["796b9511"]},
    {"name": "Priest Titan Boots Reb+20", "max_price": 5000000000, "item_ids": ["7a6b9511"]},
    {"name": "Priest Titan Boots Reb+21", "max_price": 5000000000, "item_ids": ["7b6b9511"]},
    {"name": "Priest Titan Gauntlets +6", "max_price": 3000000, "item_ids": ["e6d0fc10"]},
    {"name": "Priest Titan Gauntlets +7", "max_price": 10000000, "item_ids": ["e7d0fc10"]},
    {"name": "Priest Titan Gauntlets +8", "max_price": 220000000, "item_ids": ["e8d0fc10"]},
    {"name": "Priest Titan Gauntlets +9", "max_price": 2000000000, "item_ids": ["e9d0fc10"]},
    {"name": "Priest Titan Gauntlets +10", "max_price": 5000000000, "item_ids": ["ead0fc10"]},
    {"name": "Priest Half Guard Helmet +7", "max_price": 1000000, "item_ids": ["3f06cf10", "4906cf10"]},
    {"name": "Priest Half Guard Helmet +8", "max_price": 15000000, "item_ids": ["4006cf10", "4a06cf10"]},
    {"name": "Priest Half Guard Helmet +9", "max_price": 220000000, "item_ids": ["4106cf10", "4b06cf10"]},
    {"name": "Priest Half Guard Helmet +10", "max_price": 5000000000, "item_ids": ["4206cf10", "4c06cf10"]},
    {"name": "Priest Half Guard Pauldron +7", "max_price": 1000000, "item_ids": ["79fece10", "6ffece10"]},
    {"name": "Priest Half Guard Pauldron +8", "max_price": 15000000, "item_ids": ["7afece10", "70fece10"]},
    {"name": "Priest Half Guard Pauldron +9", "max_price": 220000000, "item_ids": ["7bfece10", "71fece10"]},
    {"name": "Priest Half Guard Pauldron +10", "max_price": 5000000000, "item_ids": ["7cfece10", "72fece10"]},
    {"name": "Priest Half Guard Pads +7", "max_price": 1000000, "item_ids": ["5702cf10", "6102cf10"]},
    {"name": "Priest Half Guard Pads +8", "max_price": 15000000, "item_ids": ["5802cf10", "6202cf10"]},
    {"name": "Priest Half Guard Pads +9", "max_price": 220000000, "item_ids": ["5902cf10", "6302cf10"]},
    {"name": "Priest Half Guard Pads +10", "max_price": 5000000000, "item_ids": ["5a02cf10", "6402cf10"]},
    {"name": "Priest Half Guard Boots +7", "max_price": 1000000, "item_ids": ["0f0ecf10", "190ecf10"]},
    {"name": "Priest Half Guard Boots +8", "max_price": 15000000, "item_ids": ["1a0ecf10", "100ecf10"]},
    {"name": "Priest Half Guard Boots +9", "max_price": 220000000, "item_ids": ["1b0ecf10", "110ecf10"]},
    {"name": "Priest Half Guard Boots +10", "max_price": 5000000000, "item_ids": ["1c0ecf10", "120ecf10"]},
    {"name": "Priest Half Guard Gauntlets +7", "max_price": 1000000, "item_ids": ["270acf10", "310acf10"]},
    {"name": "Priest Half Guard Gauntlets +8", "max_price": 15000000, "item_ids": ["280acf10", "320acf10"]},
    {"name": "Priest Half Guard Gauntlets +9", "max_price": 220000000, "item_ids": ["290acf10", "330acf10"]},
    {"name": "Priest Half Guard Gauntlets +10", "max_price": 5000000000, "item_ids": ["2a0acf10", "340acf10"]},
    {"name": "Priest Fabric Helmet +7", "max_price": 1000000, "item_ids": ["09c4bf10", "ffc3bf10"]},
    {"name": "Priest Fabric Helmet +8", "max_price": 15000000, "item_ids": ["0ac4bf10", "00c3bf10"]},
    {"name": "Priest Fabric Helmet +9", "max_price": 220000000, "item_ids": ["0bc4bf10", "01c3bf10"]},
    {"name": "Priest Fabric Helmet +10", "max_price": 5000000000, "item_ids": ["0cc4bf10", "02c3bf10"]},
    {"name": "Priest Fabric Pauldron +7", "max_price": 1000000, "item_ids": ["39bcbf10", "2fbcbf10"]},
    {"name": "Priest Fabric Pauldron +8", "max_price": 15000000, "item_ids": ["3abcbf10", "30bcbf10"]},
    {"name": "Priest Fabric Pauldron +9", "max_price": 220000000, "item_ids": ["3bbcbf10", "31bcbf10"]},
    {"name": "Priest Fabric Pauldron +10", "max_price": 5000000000, "item_ids": ["3cbcbf10", "32bcbf10"]},
    {"name": "Priest Fabric Pads +7", "max_price": 1000000, "item_ids": ["21c0bf10", "17c0bf10"]},
    {"name": "Priest Fabric Pads +8", "max_price": 15000000, "item_ids": ["22c0bf10", "18c0bf10"]},
    {"name": "Priest Fabric Pads +9", "max_price": 220000000, "item_ids": ["23c0bf10", "19c0bf10"]},
    {"name": "Priest Fabric Pads +10", "max_price": 5000000000, "item_ids": ["24c0bf10", "1ac0bf10"]},
    {"name": "Priest Fabric Boots +7", "max_price": 1000000, "item_ids": ["cfcbbf10", "d9cbbf10"]},
    {"name": "Priest Fabric Boots +8", "max_price": 15000000, "item_ids": ["dacbbf10", "d0cbbf10"]},
    {"name": "Priest Fabric Boots +9", "max_price": 220000000, "item_ids": ["dbcbbf10", "d1cbbf10"]},
    {"name": "Priest Fabric Boots +10", "max_price": 5000000000, "item_ids": ["dccbbf10", "d2cbbf10"]},
    {"name": "Priest Fabric Gauntlets +7", "max_price": 1000000, "item_ids": ["dbc9bf10", "f1c7bf10"]},
    {"name": "Priest Fabric Gauntlets +8", "max_price": 15000000, "item_ids": ["f2c7bf10", "dcc9bf10"]},
    {"name": "Priest Fabric Gauntlets +9", "max_price": 220000000, "item_ids": ["f3c7bf10", "ddc9bf10"]},
    {"name": "Priest Fabric Gauntlets +10", "max_price": 5000000000, "item_ids": ["f4c7bf10", "dec9bf10"]},
    {"name": "Priest Elder Armor Boots +5", "max_price": 50000000, "item_ids": ["4dfcfc22", "41fefc22"]},
    {"name": "Priest Elder Armor Boots +6", "max_price": 50000000, "item_ids": ["4efcfc22", "42fefc22"]},
    {"name": "Priest Elder Armor Boots +7", "max_price": 220000000, "item_ids": ["43fefc22", "4ffcfc22"]},
    {"name": "Priest Elder Armor Boots +8", "max_price": 220000000, "item_ids": ["50fcfc22", "44fefc22"]},
    {"name": "Priest Elder Armor Boots Reb+1", "max_price": 220000000, "item_ids": ["e7929523"]},
    {"name": "Priest Elder Armor Boots Reb+2", "max_price": 220000000, "item_ids": ["e8929523"]},
    {"name": "Priest Elder Armor Boots Reb+3", "max_price": 220000000, "item_ids": ["e9929523"]},
    {"name": "Priest Elder Armor Boots Reb+4", "max_price": 220000000, "item_ids": ["ea929523"]},
    {"name": "Priest Elder Armor Boots Reb+5", "max_price": 220000000, "item_ids": ["eb929523"]},
    {"name": "Priest Elder Armor Helmet +5", "max_price": 50000000, "item_ids": ["7df4fc22", "71f6fc22"]},
    {"name": "Priest Elder Armor Helmet +6", "max_price": 50000000, "item_ids": ["7ef4fc22", "72f6fc22"]},
    {"name": "Priest Elder Armor Helmet +7", "max_price": 220000000, "item_ids": ["73f6fc22", "7ff4fc22"]},
    {"name": "Priest Elder Armor Helmet +8", "max_price": 220000000, "item_ids": ["80f4fc22", "74f6fc22"]},
    {"name": "Priest Elder Armor Helmet Reb+1", "max_price": 220000000, "item_ids": []},
    {"name": "Priest Elder Armor Pauldron +5", "max_price": 50000000, "item_ids": ["adecfc22", "a1eefc22"]},
    {"name": "Priest Elder Armor Pauldron +6", "max_price": 50000000, "item_ids": ["aeecfc22", "a2eefc22"]},
    {"name": "Priest Elder Armor Pauldron +7", "max_price": 220000000, "item_ids": ["a3eefc22", "afecfc22"]},
    {"name": "Priest Elder Armor Pauldron +8", "max_price": 220000000, "item_ids": ["b0ecfc22", "a4eefc22"]},
    {"name": "Priest Elder Armor Pauldron Reb+1", "max_price": 220000000, "item_ids": ["47839523"]},
    {"name": "Priest Elder Armor Pauldron Reb+2", "max_price": 220000000, "item_ids": ["48839523"]},
    {"name": "Priest Elder Armor Pauldron Reb+3", "max_price": 220000000, "item_ids": ["49839523"]},
    {"name": "Priest Elder Armor Pauldron Reb+4", "max_price": 220000000, "item_ids": ["4a839523"]},
    {"name": "Priest Elder Armor Pauldron Reb+5", "max_price": 220000000, "item_ids": ["4b839523"]},
    {"name": "Priest Elder Armor Pads +5", "max_price": 50000000, "item_ids": ["95f0fc22", "89f2fc22"]},
    {"name": "Priest Elder Armor Pads +6", "max_price": 50000000, "item_ids": ["8af2fc22", "96f0fc22"]},
    {"name": "Priest Elder Armor Pads +7", "max_price": 220000000, "item_ids": ["8bf2fc22", "97f0fc22"]},
    {"name": "Priest Elder Armor Pads +8", "max_price": 220000000, "item_ids": ["8cf2fc22", "98f0fc22"]},
    {"name": "Priest Elder Armor Pads Reb+1", "max_price": 220000000, "item_ids": ["2f879523"]},
    {"name": "Priest Elder Armor Pads Reb+2", "max_price": 220000000, "item_ids": ["30879523"]},
    {"name": "Priest Elder Armor Pads Reb+3", "max_price": 220000000, "item_ids": ["31879523"]},
    {"name": "Priest Elder Armor Pads Reb+4", "max_price": 220000000, "item_ids": ["32879523"]},
    {"name": "Priest Elder Armor Pads Reb+5", "max_price": 220000000, "item_ids": ["33879523"]},
    {"name": "Priest Elder Armor Gauntlets +5", "max_price": 50000000, "item_ids": ["6ff8fc22", "59fafc22"]},
    {"name": "Priest Elder Armor Gauntlets +6", "max_price": 50000000, "item_ids": ["70f8fc22", "5afafc22"]},
    {"name": "Priest Elder Armor Gauntlets +7", "max_price": 220000000, "item_ids": ["71f8fc22", "5bfafc22"]},
    {"name": "Priest Elder Armor Gauntlets +8", "max_price": 220000000, "item_ids": ["72f8fc22", "5cfafc22"]},
    {"name": "Priest Elder Armor Gauntlets Reb+1", "max_price": 220000000, "item_ids": ["ff8e9523"]},
    {"name": "Priest Elder Armor Gauntlets Reb+2", "max_price": 220000000, "item_ids": ["008e9523"]},
    {"name": "Priest Elder Armor Gauntlets Reb+3", "max_price": 220000000, "item_ids": ["018e9523"]},
    {"name": "Priest Elder Armor Gauntlets Reb+4", "max_price": 220000000, "item_ids": ["028e9523"]},
    {"name": "Priest Elder Armor Gauntlets Reb+5", "max_price": 220000000, "item_ids": ["038e9523"]},
    {"name": "Mage Holy Titan Helmet +5", "max_price": 3000000, "item_ids": ["3de2da0f"]},
    {"name": "Mage Holy Titan Helmet +6", "max_price": 10000000, "item_ids": ["3ee2da0f"]},
    {"name": "Mage Holy Titan Helmet +7", "max_price": 30000000, "item_ids": ["3fe2da0f"]},
    {"name": "Mage Holy Titan Helmet +8", "max_price": 220000000, "item_ids": ["40e2da0f"]},
    {"name": "Mage Holy Titan Helmet +9", "max_price": 2000000000, "item_ids": ["41e2da0f"]},
    {"name": "Mage Holy Titan Helmet +10", "max_price": 5000000000, "item_ids": ["42e2da0f"]},
    {"name": "Mage Holy Titan Pauldron +5", "max_price": 3000000, "item_ids": ["6ddada0f"]},
    {"name": "Mage Holy Titan Pauldron +6", "max_price": 10000000, "item_ids": ["6edada0f"]},
    {"name": "Mage Holy Titan Pauldron +7", "max_price": 30000000, "item_ids": ["6fdada0f"]},
    {"name": "Mage Holy Titan Pauldron +8", "max_price": 220000000, "item_ids": ["70dada0f"]},
    {"name": "Mage Holy Titan Pauldron +9", "max_price": 2000000000, "item_ids": ["71dada0f"]},
    {"name": "Mage Holy Titan Pauldron +10", "max_price": 5000000000, "item_ids": ["72dada0f"]},
    {"name": "Mage Holy Titan Pauldron Reb+1", "max_price": 30000000, "item_ids": ["07717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+2", "max_price": 30000000, "item_ids": ["08717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+3", "max_price": 100000000, "item_ids": ["09717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+4", "max_price": 220000000, "item_ids": ["0a717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+5", "max_price": 220000000, "item_ids": ["0b717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+6", "max_price": 350000000, "item_ids": ["0c717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+7", "max_price": 350000000, "item_ids": ["0d717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+8", "max_price": 500000000, "item_ids": ["0e717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+9", "max_price": 500000000, "item_ids": ["0f717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+10", "max_price": 500000000, "item_ids": ["10717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+11", "max_price": 2000000000, "item_ids": ["11717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+12", "max_price": 2000000000, "item_ids": ["12717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+13", "max_price": 2000000000, "item_ids": ["13717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+14", "max_price": 5000000000, "item_ids": ["14717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+15", "max_price": 5000000000, "item_ids": ["15717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+16", "max_price": 5000000000, "item_ids": ["16717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+17", "max_price": 5000000000, "item_ids": ["17717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+18", "max_price": 5000000000, "item_ids": ["18717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+19", "max_price": 5000000000, "item_ids": ["19717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+20", "max_price": 5000000000, "item_ids": ["1a717310"]},
    {"name": "Mage Holy Titan Pauldron Reb+21", "max_price": 5000000000, "item_ids": ["1b717310"]},
    {"name": "Mage Holy Titan Pads +5", "max_price": 3000000, "item_ids": ["49e0da0f", "55deda0f"]},
    {"name": "Mage Holy Titan Pads +6", "max_price": 10000000, "item_ids": ["4ae0da0f", "56deda0f"]},
    {"name": "Mage Holy Titan Pads +7", "max_price": 30000000, "item_ids": ["4be0da0f", "57deda0f"]},
    {"name": "Mage Holy Titan Pads +8", "max_price": 220000000, "item_ids": ["4ce0da0f", "58deda0f"]},
    {"name": "Mage Holy Titan Pads +9", "max_price": 2000000000, "item_ids": ["4de0da0f", "59deda0f"]},
    {"name": "Mage Holy Titan Pads +10", "max_price": 5000000000, "item_ids": ["4ee0da0f", "5adeda0f"]},
    {"name": "Mage Holy Titan Boots +5", "max_price": 3000000, "item_ids": ["0deada0f"]},
    {"name": "Mage Holy Titan Boots +6", "max_price": 10000000, "item_ids": ["0eeada0f"]},
    {"name": "Mage Holy Titan Boots +7", "max_price": 30000000, "item_ids": ["0feada0f"]},
    {"name": "Mage Holy Titan Boots +8", "max_price": 220000000, "item_ids": ["10eada0f"]},
    {"name": "Mage Holy Titan Boots +9", "max_price": 2000000000, "item_ids": ["11eada0f"]},
    {"name": "Mage Holy Titan Boots +10", "max_price": 5000000000, "item_ids": ["12eada0f"]},
    {"name": "Mage Holy Titan Gauntlets +5", "max_price": 3000000, "item_ids": ["19e8da0f", "25e6da0f"]},
    {"name": "Mage Holy Titan Gauntlets +6", "max_price": 10000000, "item_ids": ["1ae8da0f", "26e6da0f"]},
    {"name": "Mage Holy Titan Gauntlets +7", "max_price": 30000000, "item_ids": ["1be8da0f", "27e6da0f"]},
    {"name": "Mage Holy Titan Gauntlets +8", "max_price": 220000000, "item_ids": ["1ce8da0f", "28e6da0f"]},
    {"name": "Mage Holy Titan Gauntlets +9", "max_price": 2000000000, "item_ids": ["1de8da0f", "29e6da0f"]},
    {"name": "Mage Holy Titan Gauntlets +10", "max_price": 5000000000, "item_ids": ["1ee8da0f", "2ae6da0f"]},
    {"name": "Mage Holy Titan Gauntlets Reb+1", "max_price": 30000000, "item_ids": ["bf7c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+2", "max_price": 30000000, "item_ids": ["c07c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+3", "max_price": 100000000, "item_ids": ["c17c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+4", "max_price": 220000000, "item_ids": ["c27c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+5", "max_price": 220000000, "item_ids": ["c37c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+6", "max_price": 220000000, "item_ids": ["c47c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+7", "max_price": 220000000, "item_ids": ["c57c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+8", "max_price": 500000000, "item_ids": ["c67c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+9", "max_price": 500000000, "item_ids": ["c77c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+10", "max_price": 1000000000500000000, "item_ids": ["c87c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+11", "max_price": 2000000000, "item_ids": ["c97c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+12", "max_price": 2000000000, "item_ids": ["ca7c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+13", "max_price": 2000000000, "item_ids": ["cb7c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+14", "max_price": 5000000000, "item_ids": ["cc7c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+15", "max_price": 5000000000, "item_ids": ["cd7c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+16", "max_price": 5000000000, "item_ids": ["ce7c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+17", "max_price": 5000000000, "item_ids": ["cf7c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+18", "max_price": 5000000000, "item_ids": ["d07c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+19", "max_price": 5000000000, "item_ids": ["d17c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+20", "max_price": 5000000000, "item_ids": ["d27c7310"]},
    {"name": "Mage Holy Titan Gauntlets Reb+21", "max_price": 5000000000, "item_ids": ["d37c7310"]},
    {"name": "Mage Titan Helmet +7", "max_price": 10000000, "item_ids": ["ff9fcb0f", "f3a1cb0f"]},
    {"name": "Mage Titan Helmet +8", "max_price": 220000000, "item_ids": ["009fcb0f", "f4a1cb0f"]},
    {"name": "Mage Titan Helmet +9", "max_price": 1000000000, "item_ids": ["019fcb0f", "f5a1cb0f"]},
    {"name": "Mage Titan Helmet +10", "max_price": 5000000000, "item_ids": ["029fcb0f", "f6a1cb0f"]},
    {"name": "Mage Titan Helmet Reb+1", "max_price": 10000000, "item_ids": ["97366410"]},
    {"name": "Mage Titan Helmet Reb+2", "max_price": 10000000, "item_ids": ["98366410"]},
    {"name": "Mage Titan Helmet Reb+3", "max_price": 40000000, "item_ids": ["99366410"]},
    {"name": "Mage Titan Helmet Reb+4", "max_price": 40000000, "item_ids": ["9a366410"]},
    {"name": "Mage Titan Helmet Reb+5", "max_price": 220000000, "item_ids": ["9b366410"]},
    {"name": "Mage Titan Helmet Reb+6", "max_price": 220000000, "item_ids": ["9c366410"]},
    {"name": "Mage Titan Helmet Reb+7", "max_price": 220000000, "item_ids": ["9d366410"]},
    {"name": "Mage Titan Helmet Reb+8", "max_price": 500000000, "item_ids": ["9e366410"]},
    {"name": "Mage Titan Helmet Reb+9", "max_price": 500000000, "item_ids": ["9f366410"]},
    {"name": "Mage Titan Helmet Reb+10", "max_price": 1000000000, "item_ids": ["a0366410"]},
    {"name": "Mage Titan Helmet Reb+11", "max_price": 1000000000, "item_ids": ["a1366410"]},
    {"name": "Mage Titan Helmet Reb+12", "max_price": 1000000000, "item_ids": ["a2366410"]},
    {"name": "Mage Titan Helmet Reb+13", "max_price": 1000000000, "item_ids": ["a3366410"]},
    {"name": "Mage Titan Helmet Reb+14", "max_price": 4000000000, "item_ids": ["a4366410"]},
    {"name": "Mage Titan Helmet Reb+15", "max_price": 5000000000, "item_ids": ["a5366410"]},
    {"name": "Mage Titan Helmet Reb+16", "max_price": 5000000000, "item_ids": ["a6366410"]},
    {"name": "Mage Titan Helmet Reb+17", "max_price": 5000000000, "item_ids": ["a7366410"]},
    {"name": "Mage Titan Helmet Reb+18", "max_price": 5000000000, "item_ids": ["a8366410"]},
    {"name": "Mage Titan Helmet Reb+19", "max_price": 5000000000, "item_ids": ["a9366410"]},
    {"name": "Mage Titan Helmet Reb+20", "max_price": 5000000000, "item_ids": ["aa366410"]},
    {"name": "Mage Titan Helmet Reb+21", "max_price": 5000000000, "item_ids": ["ab366410"]},
    {"name": "Mage Titan Pauldron +7", "max_price": 10000000, "item_ids": ["2f98cb0f", "239acb0f"]},
    {"name": "Mage Titan Pauldron +8", "max_price": 220000000, "item_ids": ["3098cb0f", "249acb0f"]},
    {"name": "Mage Titan Pauldron +9", "max_price": 1000000000, "item_ids": ["3198cb0f", "259acb0f"]},
    {"name": "Mage Titan Pauldron +10", "max_price": 5000000000, "item_ids": ["3298cb0f", "269acb0f"]},
    {"name": "Mage Titan Pauldron Reb+1", "max_price": 10000000, "item_ids": ["c72e6410"]},
    {"name": "Mage Titan Pauldron Reb+2", "max_price": 10000000, "item_ids": ["c82e6410"]},
    {"name": "Mage Titan Pauldron Reb+3", "max_price": 40000000, "item_ids": ["c92e6410"]},
    {"name": "Mage Titan Pauldron Reb+4", "max_price": 40000000, "item_ids": ["ca2e6410"]},
    {"name": "Mage Titan Pauldron Reb+5", "max_price": 220000000, "item_ids": ["cb2e6410"]},
    {"name": "Mage Titan Pauldron Reb+6", "max_price": 220000000, "item_ids": ["cc2e6410"]},
    {"name": "Mage Titan Pauldron Reb+7", "max_price": 220000000, "item_ids": ["cd2e6410"]},
    {"name": "Mage Titan Pauldron Reb+8", "max_price": 500000000, "item_ids": ["ce2e6410"]},
    {"name": "Mage Titan Pauldron Reb+9", "max_price": 500000000, "item_ids": ["cf2e6410"]},
    {"name": "Mage Titan Pauldron Reb+10", "max_price": 1000000000, "item_ids": ["d02e6410"]},
    {"name": "Mage Titan Pauldron Reb+11", "max_price": 1000000000, "item_ids": ["d12e6410"]},
    {"name": "Mage Titan Pauldron Reb+12", "max_price": 1000000000, "item_ids": ["d22e6410"]},
    {"name": "Mage Titan Pauldron Reb+13", "max_price": 1000000000, "item_ids": ["d32e6410"]},
    {"name": "Mage Titan Pauldron Reb+14", "max_price": 4000000000, "item_ids": ["d42e6410"]},
    {"name": "Mage Titan Pauldron Reb+15", "max_price": 5000000000, "item_ids": ["d52e6410"]},
    {"name": "Mage Titan Pauldron Reb+16", "max_price": 5000000000, "item_ids": ["d62e6410"]},
    {"name": "Mage Titan Pauldron Reb+17", "max_price": 5000000000, "item_ids": ["d72e6410"]},
    {"name": "Mage Titan Pauldron Reb+18", "max_price": 5000000000, "item_ids": ["d82e6410"]},
    {"name": "Mage Titan Pauldron Reb+19", "max_price": 5000000000, "item_ids": ["d92e6410"]},
    {"name": "Mage Titan Pauldron Reb+20", "max_price": 5000000000, "item_ids": ["da2e6410"]},
    {"name": "Mage Titan Pauldron Reb+21", "max_price": 5000000000, "item_ids": ["db2e6410"]},
    {"name": "Mage Titan Pads +7", "max_price": 10000000, "item_ids": ["0b9ecb0f", "179ccb0f"]},
    {"name": "Mage Titan Pads +8", "max_price": 220000000, "item_ids": ["0c9ecb0f", "189ccb0f"]},
    {"name": "Mage Titan Pads +9", "max_price": 1000000000, "item_ids": ["0d9ecb0f", "199ccb0f"]},
    {"name": "Mage Titan Pads +10", "max_price": 5000000000, "item_ids": ["0e9ecb0f", "1a9ccb0f"]},
    {"name": "Mage Titan Pads Reb+1", "max_price": 10000000, "item_ids": ["af326410"]},
    {"name": "Mage Titan Pads Reb+2", "max_price": 10000000, "item_ids": ["b0326410"]},
    {"name": "Mage Titan Pads Reb+3", "max_price": 40000000, "item_ids": ["b1326410"]},
    {"name": "Mage Titan Pads Reb+4", "max_price": 40000000, "item_ids": ["b2326410"]},
    {"name": "Mage Titan Pads Reb+5", "max_price": 220000000, "item_ids": ["b3326410"]},
    {"name": "Mage Titan Pads Reb+6", "max_price": 220000000, "item_ids": ["b4326410"]},
    {"name": "Mage Titan Pads Reb+7", "max_price": 220000000, "item_ids": ["b5326410"]},
    {"name": "Mage Titan Pads Reb+8", "max_price": 500000000, "item_ids": ["b6326410"]},
    {"name": "Mage Titan Pads Reb+9", "max_price": 500000000, "item_ids": ["b7326410"]},
    {"name": "Mage Titan Pads Reb+10", "max_price": 1000000000, "item_ids": ["b8326410"]},
    {"name": "Mage Titan Pads Reb+11", "max_price": 1000000000, "item_ids": ["b9326410"]},
    {"name": "Mage Titan Pads Reb+12", "max_price": 1000000000, "item_ids": ["ba326410"]},
    {"name": "Mage Titan Pads Reb+13", "max_price": 1000000000, "item_ids": ["bb326410"]},
    {"name": "Mage Titan Pads Reb+14", "max_price": 5000000000, "item_ids": ["bc326410"]},
    {"name": "Mage Titan Pads Reb+15", "max_price": 5000000000, "item_ids": ["bd326410"]},
    {"name": "Mage Titan Pads Reb+16", "max_price": 5000000000, "item_ids": ["be326410"]},
    {"name": "Mage Titan Pads Reb+17", "max_price": 5000000000, "item_ids": ["bf326410"]},
    {"name": "Mage Titan Pads Reb+18", "max_price": 5000000000, "item_ids": ["c0326410"]},
    {"name": "Mage Titan Pads Reb+19", "max_price": 5000000000, "item_ids": ["c1326410"]},
    {"name": "Mage Titan Pads Reb+20", "max_price": 5000000000, "item_ids": ["c2326410"]},
    {"name": "Mage Titan Pads Reb+21", "max_price": 5000000000, "item_ids": ["c3326410"]},
    {"name": "Mage Titan Boots +7", "max_price": 10000000, "item_ids": ["c3a9cb0f", "cfa7cb0f"]},
    {"name": "Mage Titan Boots +8", "max_price": 220000000, "item_ids": ["c4a9cb0f", "d0a7cb0f"]},
    {"name": "Mage Titan Boots +9", "max_price": 1000000000, "item_ids": ["c5a9cb0f", "d1a7cb0f"]},
    {"name": "Mage Titan Boots +10", "max_price": 5000000000, "item_ids": ["c6a9cb0f", "d2a7cb0f"]},
    {"name": "Mage Titan Gauntlets +7", "max_price": 10000000, "item_ids": ["dba5cb0f"]},
    {"name": "Mage Titan Gauntlets +8", "max_price": 220000000, "item_ids": ["dca5cb0f"]},
    {"name": "Mage Titan Gauntlets +9", "max_price": 1000000000, "item_ids": ["dda5cb0f"]},
    {"name": "Mage Titan Gauntlets +10", "max_price": 5000000000, "item_ids": ["dea5cb0f"]},
    {"name": "Mage Half Guard Helmet +7", "max_price": 1000000, "item_ids": ["51db9d0f", "3fd99d0f"]},
    {"name": "Mage Half Guard Helmet +8", "max_price": 15000000, "item_ids": ["52db9d0f", "40d99d0f"]},
    {"name": "Mage Half Guard Helmet +9", "max_price": 220000000, "item_ids": ["41d99d0f", "53db9d0f"]},
    {"name": "Mage Half Guard Helmet +10", "max_price": 5000000000, "item_ids": ["42d99d0f", "54db9d0f"]},
    {"name": "Mage Half Guard Pauldron +7", "max_price": 1000000, "item_ids": ["6fd19d0f"]},
    {"name": "Mage Half Guard Pauldron +8", "max_price": 15000000, "item_ids": ["70d19d0f"]},
    {"name": "Mage Half Guard Pauldron +9", "max_price": 220000000, "item_ids": ["71d19d0f"]},
    {"name": "Mage Half Guard Pauldron +10", "max_price": 5000000000, "item_ids": ["72d19d0f"]},
    {"name": "Mage Half Guard Pads +7", "max_price": 1000000, "item_ids": ["57d59d0f"]},
    {"name": "Mage Half Guard Pads +8", "max_price": 15000000, "item_ids": ["58d59d0f"]},
    {"name": "Mage Half Guard Pads +9", "max_price": 220000000, "item_ids": ["59d59d0f"]},
    {"name": "Mage Half Guard Pads +10", "max_price": 5000000000, "item_ids": ["5ad59d0f"]},
    {"name": "Mage Half Guard Boots +7", "max_price": 1000000, "item_ids": ["21e39d0f", "0fe19d0f"]},
    {"name": "Mage Half Guard Boots +8", "max_price": 15000000, "item_ids": ["10e19d0f", "22e39d0f"]},
    {"name": "Mage Half Guard Boots +9", "max_price": 220000000, "item_ids": ["11e19d0f", "23e39d0f"]},
    {"name": "Mage Half Guard Boots +10", "max_price": 5000000000, "item_ids": ["12e19d0f", "24e39d0f"]},
    {"name": "Mage Half Guard Gauntlets +7", "max_price": 1000000, "item_ids": ["39df9d0f", "27dd9d0f"]},
    {"name": "Mage Half Guard Gauntlets +8", "max_price": 15000000, "item_ids": ["28dd9d0f", "3adf9d0f"]},
    {"name": "Mage Half Guard Gauntlets +9", "max_price": 220000000, "item_ids": ["29dd9d0f", "3bdf9d0f"]},
    {"name": "Mage Half Guard Gauntlets +10", "max_price": 5000000000, "item_ids": ["2add9d0f", "3cdf9d0f"]},
    {"name": "Mage Fabric Helmet +7", "max_price": 1000000, "item_ids": ["ff968e0f", "11998e0f"]},
    {"name": "Mage Fabric Helmet +8", "max_price": 15000000, "item_ids": ["00968e0f", "12998e0f"]},
    {"name": "Mage Fabric Helmet +9", "max_price": 220000000, "item_ids": ["01968e0f", "13998e0f"]},
    {"name": "Mage Fabric Helmet +10", "max_price": 5000000000, "item_ids": ["02968e0f", "14998e0f"]},
    {"name": "Mage Fabric Pauldron +7", "max_price": 1000000, "item_ids": ["81d39d0f", "23918e0f", "41918e0f"]},
    {"name": "Mage Fabric Pauldron +8", "max_price": 15000000, "item_ids": ["82d39d0f", "24918e0f", "42918e0f"]},
    {"name": "Mage Fabric Pauldron +9", "max_price": 220000000, "item_ids": ["43918e0f", "83d39d0f", "25918e0f"]},
    {"name": "Mage Fabric Pauldron +10", "max_price": 5000000000, "item_ids": ["44918e0f", "84d39d0f", "26918e0f"]},
    {"name": "Mage Fabric Pads +7", "max_price": 1000000, "item_ids": ["17938e0f", "29958e0f"]},
    {"name": "Mage Fabric Pads +8", "max_price": 15000000, "item_ids": ["18938e0f", "2a958e0f"]},
    {"name": "Mage Fabric Pads +9", "max_price": 220000000, "item_ids": ["19938e0f", "2b958e0f"]},
    {"name": "Mage Fabric Pads +10", "max_price": 5000000000, "item_ids": ["1a938e0f", "2c958e0f"]},
    {"name": "Mage Fabric Boots +7", "max_price": 1000000, "item_ids": ["e1a08e0f", "cf9e8e0f", "c3a08e0f"]},
    {"name": "Mage Fabric Boots +8", "max_price": 15000000, "item_ids": ["e2a08e0f", "d09e8e0f", "c4a08e0f"]},
    {"name": "Mage Fabric Boots +9", "max_price": 220000000, "item_ids": ["e3a08e0f", "d19e8e0f", "c5a08e0f"]},
    {"name": "Mage Fabric Boots +10", "max_price": 5000000000, "item_ids": ["e4a08e0f", "d29e8e0f", "c6a08e0f"]},
    {"name": "Mage Fabric Gauntlets +7", "max_price": 1000000, "item_ids": ["db9c8e0f", "f99c8e0f"]},
    {"name": "Mage Fabric Gauntlets +8", "max_price": 15000000, "item_ids": ["dc9c8e0f", "fa9c8e0f"]},
    {"name": "Mage Fabric Gauntlets +9", "max_price": 220000000, "item_ids": ["dd9c8e0f", "fb9c8e0f"]},
    {"name": "Mage Fabric Gauntlets +10", "max_price": 5000000000, "item_ids": ["de9c8e0f", "fc9c8e0f"]},
    {"name": "Mage Elder Armor Boots +5", "max_price": 50000000, "item_ids": ["4dcfcb21", "5fd1cb21"]},
    {"name": "Mage Elder Armor Boots +6", "max_price": 50000000, "item_ids": ["4ecfcb21", "60d1cb21"]},
    {"name": "Mage Elder Armor Boots +7", "max_price": 220000000, "item_ids": ["4fcfcb21", "61d1cb21"]},
    {"name": "Mage Elder Armor Boots +8", "max_price": 220000000, "item_ids": ["62d1cb21", "50cfcb21"]},
    {"name": "Mage Elder Armor Helmet +5", "max_price": 50000000, "item_ids": ["71c9cb21"]},
    {"name": "Mage Elder Armor Helmet +6", "max_price": 50000000, "item_ids": ["72c9cb21"]},
    {"name": "Mage Elder Armor Helmet +7", "max_price": 220000000, "item_ids": ["73c9cb21"]},
    {"name": "Mage Elder Armor Helmet +8", "max_price": 220000000, "item_ids": ["74c9cb21"]},
    {"name": "Mage Elder Armor Pauldron +5", "max_price": 50000000, "item_ids": ["a1c1cb21", "adbfcb21"]},
    {"name": "Mage Elder Armor Pauldron +6", "max_price": 50000000, "item_ids": ["a2c1cb21", "aebfcb21"]},
    {"name": "Mage Elder Armor Pauldron +7", "max_price": 220000000, "item_ids": ["a3c1cb21", "afbfcb21"]},
    {"name": "Mage Elder Armor Pauldron +8", "max_price": 220000000, "item_ids": ["a4c1cb21", "b0bfcb21"]},
    {"name": "Mage Elder Armor Pauldron Reb+1", "max_price": 220000000, "item_ids": []},
    {"name": "Mage Elder Armor Pauldron Reb+2", "max_price": 220000000, "item_ids": []},
    {"name": "Mage Elder Armor Pauldron Reb+3", "max_price": 300000000, "item_ids": []},
    {"name": "Mage Elder Armor Pauldron Reb+4", "max_price": 1000000000, "item_ids": []},
    {"name": "Mage Elder Armor Pauldron Reb+5", "max_price": 5000000000, "item_ids": []},
    {"name": "Mage Elder Armor Pads +5", "max_price": 50000000, "item_ids": ["95c3cb21"]},
    {"name": "Mage Elder Armor Pads +6", "max_price": 50000000, "item_ids": ["96c3cb21"]},
    {"name": "Mage Elder Armor Pads +7", "max_price": 220000000, "item_ids": ["97c3cb21"]},
    {"name": "Mage Elder Armor Pads +8", "max_price": 220000000, "item_ids": ["98c3cb21"]},
    {"name": "Mage Elder Armor Gauntlets +5", "max_price": 50000000, "item_ids": ["65cbcb21", "59cdcb21"]},
    {"name": "Mage Elder Armor Gauntlets +6", "max_price": 50000000, "item_ids": ["66cbcb21", "5acdcb21"]},
    {"name": "Mage Elder Armor Gauntlets +7", "max_price": 220000000, "item_ids": ["5bcdcb21", "67cbcb21"]},
    {"name": "Mage Elder Armor Gauntlets +8", "max_price": 220000000, "item_ids": ["68cbcb21", "5ccdcb21"]},
    {"name": "SKILL QUEST +0", "max_price": 7000000, "item_ids": ["c03da516"]},
    {"name": "Low Mastery CR BOX +0", "max_price": 5000000, "item_ids": ["88f47206"]},
    {"name": "Middle Mastery CR BOX +0", "max_price": 5000000, "item_ids": ["70f87206"]},
    {"name": "High Mastery CR BOX +0", "max_price": 5000000, "item_ids": ["58fc7206"]},
    {"name": "NOWA BOX +0", "max_price": 10000000, "item_ids": ["68b50d0c"]},
    {"name": "Elder Armor Piece Box +0", "max_price": 100000000, "item_ids": []},
    {"name": "Diamond Box +0", "max_price": 5000000, "item_ids": []},
    {"name": "Red Chest +0", "max_price": 3000000, "item_ids": ["506e9916"]},
    {"name": "Green Chest +0", "max_price": 4000000, "item_ids": ["38729916"]},
    {"name": "Blue Chest +0", "max_price": 5000000, "item_ids": ["20769916"]},
    {"name": "Fragment of Blaze LWL 1 +0", "max_price": 1000000, "item_ids": ["401c3217"]},
    {"name": "Fragment of Mirage LWL 2 +0", "max_price": 1000000, "item_ids": ["28203217"]},
    {"name": "Fragment of Thnder LWL 3 +0", "max_price": 1000000, "item_ids": ["10243217"]},
    {"name": "Fragment of Eclipse LWL 4 +0", "max_price": 2000000, "item_ids": ["f8273217"]},
    {"name": "Fragment of Tempest LWL 5 +0", "max_price": 2000000, "item_ids": ["e02b3217"]},
    {"name": "Fragment of Aurora LWL 6 +0", "max_price": 3000000, "item_ids": ["c82f3217"]},
    {"name": "Fragment of Obsidian LWL 7 +0", "max_price": 5000000, "item_ids": ["b0333217"]},
    {"name": "Silver Gem LWL 6 +0", "max_price": 5000000, "item_ids": ["e0a83217"]},
    {"name": "Red Gem LWL 5 +0", "max_price": 4000000, "item_ids": ["c8ac3217"]},
    {"name": "Sunlight Gem LWL 4 +0", "max_price": 1000000, "item_ids": ["b0b03217"]},
    {"name": "Blue Gem LWL 3 +0", "max_price": 1000000, "item_ids": ["98b43217"]},
    {"name": "Green Gem LVL 2 +0", "max_price": 1000000, "item_ids": ["68bc3217"]},
    {"name": "Blue Spring Box +0", "max_price": 5000000, "item_ids": ["58e6391e"]},
    {"name": "Red Spring Box +0", "max_price": 5000000, "item_ids": []},
    {"name": "High CR BOX +0", "max_price": 3000000, "item_ids": ["a0f7491e"]},
    {"name": "Low CR BOX +0", "max_price": 3000000, "item_ids": ["b8704a1e"]},
    {"name": "Middle CR BOX +0", "max_price": 3000000, "item_ids": ["78344b30"]},
    {"name": "Eid Box +0", "max_price": 3000000, "item_ids": ["28824b1e"]},
    {"name": "Mystic Jewel +0", "max_price": 20000000, "item_ids": ["d02eb929"]},
    {"name": "Legendary Cape +0", "max_price": 100000000, "item_ids": ["90d57006"]},
    {"name": "Full Premium +0", "max_price": 220000000, "item_ids": ["10b6b335"]},
    {"name": "Clan Premium +0", "max_price": 220000000, "item_ids": ["d0f2c913"]},
    {"name": "Talisman +0", "max_price": 20000000, "item_ids": ["90049b16"]},
    {"name": "Lucky Tried +0", "max_price": 25000000, "item_ids": ["284ab929"]},
    {"name": "Storem Mp Pot +0", "max_price": 6000000, "item_ids": ["c0c53517"]},
    {"name": "Character Seal Scrool +0", "max_price": 220000000, "item_ids": ["98b9b02f"]},
    {"name": "Wings Voucher Coupon +0", "max_price": 30000000, "item_ids": []},
    {"name": "Piece of +5 Rogue Elder Armor 0", "max_price": 50000000, "item_ids": ["4050950c"]},
    {"name": "Piece of +5 Warrior Elder Armor 0", "max_price": 50000000, "item_ids": ["584c950c"]},
    {"name": "Piece of +5 Priest Elder Armor 0", "max_price": 20000000, "item_ids": ["1058950c"]},
    {"name": "Piece of +5 Mage Elder Armor 0", "max_price": 20000000, "item_ids": ["2854950c"]},
    {"name": "Piece of +7 Rogue Elder Armor 0", "max_price": 220000000, "item_ids": ["e05f950c"]},
    {"name": "Piece of +7 Warrior Elder Armor 0", "max_price": 220000000, "item_ids": ["f85b950c"]},
    {"name": "Piece of +7 Priest Elder Armor 0", "max_price": 220000000, "item_ids": ["b067950c"]},
    {"name": "Piece of +7 Mage Elder Armor 0", "max_price": 120000000, "item_ids": ["c863950c"]},
    {"name": "+9 Holy Upgrade Scrool +0", "max_price": 5000000000, "item_ids": ["28aef70e"]},
    {"name": "+8 Holy Upgrade Scrool +0", "max_price": 5000000000, "item_ids": ["40aaf70e"]},
    {"name": "Divine Upgrade Scrool +7 +0", "max_price": 1000000000, "item_ids": ["10b2f70e"]},
    {"name": "Gold Rod +1", "max_price": 100000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +2", "max_price": 100000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +3", "max_price": 300000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +4", "max_price": 300000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +5", "max_price": 300000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +6", "max_price": 300000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +7", "max_price": 300000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +8", "max_price": 300000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +9", "max_price": 500000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +10", "max_price": 500000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +11", "max_price": 500000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +12", "max_price": 750000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +13", "max_price": 750000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +14", "max_price": 750000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +15", "max_price": 900000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +16", "max_price": 900000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +17", "max_price": 900000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +18", "max_price": 900000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +19", "max_price": 900000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +20", "max_price": 900000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +21", "max_price": 1500000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +22", "max_price": 1500000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +23", "max_price": 5000000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +24", "max_price": 5000000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +25", "max_price": 5000000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +26", "max_price": 5000000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +27", "max_price": 5000000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +28", "max_price": 5000000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +29", "max_price": 5000000000, "item_ids": ["81b9670b"]},
    {"name": "Gold Rod +30", "max_price": 5000000000, "item_ids": ["81b9670b"]},
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

# ── ORTAK YARDIMCI ───────────────────────────────────────────────
def run_shell(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=20)
        return r
    except Exception as e:
        log(f"Shell hata: {e}")
        return None

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

# ── PCAP OKUMA (ortak) ───────────────────────────────────────────
def get_pcap_size(pcap_path):
    try:
        r = run_shell(f"su -c 'wc -c {pcap_path} 2>/dev/null'")
        if r and r.stdout:
            parts = r.stdout.decode("utf-8", errors="ignore").strip().split()
            if parts:
                return int(parts[0])
    except:
        pass
    return 0

def pull_pcap(pcap_path, local_name):
    try:
        run_shell(f"su -c 'chmod 644 {pcap_path}'")
        local = os.path.join(os.path.expanduser("~"), local_name)
        run_shell(f"su -c 'cp {pcap_path} {local} && chmod 644 {local}'")
        if os.path.exists(local) and os.path.getsize(local) > 24:
            run_shell(f"su -c 'rm -f {pcap_path}'")
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

def get_ip_start(pkt, link_type):
    """Link tipine gore IP baslangiç offsetini dondur. Gecersizse -1."""
    try:
        if link_type == 276:   # LINUX_SLL2
            if len(pkt) < 20: return -1
            et = struct.unpack(">H", pkt[0:2])[0]
            return 20 if et == 0x0800 else -1
        elif link_type == 113: # LINUX_SLL
            if len(pkt) < 16: return -1
            et = struct.unpack(">H", pkt[14:16])[0]
            return 16 if et == 0x0800 else -1
        else:                  # Ethernet
            if len(pkt) < 14: return -1
            et = struct.unpack(">H", pkt[12:14])[0]
            return 14 if et == 0x0800 else -1
    except:
        return -1

def extract_tcp_payload(pkt, link_type, src_ip=None, dst_port=None):
    """Paketten TCP payload'u al. src_ip veya dst_port filtresi opsiyonel."""
    ip_start = get_ip_start(pkt, link_type)
    if ip_start < 0: return b""
    ip = pkt[ip_start:]
    if len(ip) < 20 or (ip[0] >> 4) != 4: return b""
    if ip[9] != 6: return b""  # TCP degil
    ihl = (ip[0] & 0x0F) * 4
    # src_ip filtresi
    if src_ip:
        s = f"{ip[12]}.{ip[13]}.{ip[14]}.{ip[15]}"
        if s != src_ip: return b""
    tcp = ip[ihl:]
    if len(tcp) < 20: return b""
    # dst_port filtresi (kaynak port kontrol -- sunucudan geliyor, kaynak port = oyun sunucusu portu)
    if dst_port:
        sport = struct.unpack(">H", tcp[0:2])[0]
        if sport != dst_port: return b""
    doff = ((tcp[12] >> 4) & 0xF) * 4
    payload = tcp[doff:]
    return payload

# ════════════════════════════════════════════
#  NORMAL PAZAR (eski sistem)
# ════════════════════════════════════════════

def start_tcpdump_normal():
    log("[NORMAL] Tcpdump baslatiliyor...")
    tcpdump_bin = "/data/data/com.termux/files/usr/bin/tcpdump"
    run_shell("su -c 'killall tcpdump 2>/dev/null'")
    time.sleep(1)
    run_shell(f"su -c 'rm -f {PCAP_PATH}'")
    run_shell("su -c 'chmod 755 /data/local/tmp'")
    proc = subprocess.Popen(
        f"su -c '{tcpdump_bin} -i any -s 0 tcp -w {PCAP_PATH}'",
        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(2)
    log(f"[NORMAL] Tcpdump aktif (PID: {proc.pid})")
    return proc

def extract_server_payloads(packets, link_type=1):
    result = b""
    for pkt in packets:
        try:
            payload = extract_tcp_payload(pkt, link_type, src_ip=GAME_SERVER)
            if len(payload) >= 10:
                result += payload
        except:
            pass
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

def parse_per_packet_normal(pkts, link_type=1):
    verified = set()
    for pkt in pkts:
        try:
            data = extract_tcp_payload(pkt, link_type, src_ip=GAME_SERVER)
            if len(data) < 22: continue
            n, i = len(data), 0
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

def check_alarms_normal(records, pkts=None, link_type=1):
    if not records:
        log("[NORMAL]   Kayit bulunamadi.")
        return
    log(f"[NORMAL]   {len(records)} kayit / {len(set(r['item_id'] for r in records))} unique ID analiz ediliyor...")

    verified = None
    if pkts:
        verified = parse_per_packet_normal(pkts, link_type)
        log(f"[NORMAL]   Dogrulama: bireysel paketlerde {len(verified)} kayit bulundu")

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
            if verified is not None:
                key = (best["seller"], best["item_id"], best["price"])
                if key not in verified:
                    log(f"[NORMAL]   ! SAHTE ALARM ENGELLENDI: {alarm['name']} @ {best['price']:,} gold")
                    continue
            fire_alarm_normal(alarm["name"], best["seller"], best["price"], alarm["max_price"])
            fired += 1
        else:
            pct = best["price"] / alarm["max_price"] * 100
            log(f"[NORMAL]   x {alarm['name']:<35} {best['price']:>14,}  (esik {alarm['max_price']:,}  %{pct:.0f})")

    unknown = {iid: cheapest[iid] for iid in cheapest if iid not in all_alarm_ids}
    if unknown:
        log(f"[NORMAL]   [{len(unknown)} bilinmeyen ID pazarda goruldu]")
    if fired == 0: log("[NORMAL]   -> Esik altinda alarm yok.")
    else:          log(f"[NORMAL]   *** {fired} ALARM ATESLENEDI! ***")

def fire_alarm_normal(item_name, seller, price, max_price):
    log(f"[NORMAL] *** ALARM *** {item_name}  |  {seller}  |  {price:,} gold")
    msg = (
        "AR MARKET - NORMAL PAZAR ALARMI!\n\n"
        f"Item  : {item_name}\n"
        f"Satan : {seller}\n"
        f"Fiyat : {price:,} gold\n"
        f"Esik  : {max_price:,} gold\n\n"
        "Hemen normal pazari ac!"
    )
    send_telegram(msg)

# ════════════════════════════════════════════
#  UST PAZAR (port 19001 — yeni sistem)
# ════════════════════════════════════════════

def start_tcpdump_ust():
    log("[UST]   Tcpdump baslatiliyor (port 19001)...")
    tcpdump_bin = "/data/data/com.termux/files/usr/bin/tcpdump"
    run_shell(f"su -c 'rm -f {PCAP_PATH_UST}'")
    proc = subprocess.Popen(
        f"su -c '{tcpdump_bin} -i any -s 0 tcp port {UST_PAZAR_PORT} -w {PCAP_PATH_UST}'",
        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(2)
    log(f"[UST]   Tcpdump aktif (PID: {proc.pid})")
    return proc

def extract_ust_payloads(packets, link_type=1):
    """Ust pazar: port 19001, sunucudan gelen paketler (kaynak port = 19001)."""
    result = b""
    for pkt in packets:
        try:
            payload = extract_tcp_payload(pkt, link_type, src_ip=GAME_SERVER, dst_port=UST_PAZAR_PORT)
            if len(payload) >= 10:
                result += payload
        except:
            pass
    return result

def parse_ust_market(stream):
    """
    Frame: aa55 (2B) | frame_len (2B LE) | msgtype (4B LE) | ... header 15B total | bloklar
    Blok 29B: listing_id(4) | item_id(4) | qty+unk(9) | price(5 LE) | padding(7)
    """
    records, seen, n, i = [], set(), len(stream), 0
    while i < n - 8:
        if not (stream[i] == 0xaa and stream[i+1] == 0x55):
            i += 1; continue
        if i + 8 > n: break
        frame_len = struct.unpack_from("<H", stream, i+2)[0]
        msg_type  = struct.unpack_from("<I", stream, i+4)[0]
        if msg_type != UST_MSG_TYPE or frame_len < UST_MIN_FRAME:
            i += 2; continue
        items_start = i + UST_HEADER_SIZE
        j = items_start
        while j + UST_BLOCK_SIZE <= n:
            # Bir sonraki frame baslarsa dur
            if stream[j] == 0xaa and j+1 < n and stream[j+1] == 0x55:
                break
            item_id = stream[j+4:j+8].hex()
            price   = int.from_bytes(stream[j+17:j+22], 'little')
            if item_id != "00000000" and UST_MIN_PRICE <= price <= UST_MAX_PRICE:
                key = (item_id, price)
                if key not in seen:
                    seen.add(key)
                    records.append({"item_id": item_id, "price": price})
            j += UST_BLOCK_SIZE
        i = j if j > items_start else i + 2
    return records

def check_alarms_ust(records):
    """Ust pazar alarmlarini kontrol et. Satici adi yok, sadece item_id + price."""
    if not records:
        log("[UST]   Kayit bulunamadi.")
        return
    log(f"[UST]   {len(records)} kayit / {len(set(r['item_id'] for r in records))} unique ID analiz ediliyor...")

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
            fire_alarm_ust(alarm["name"], best["price"], alarm["max_price"])
            fired += 1
        else:
            pct = best["price"] / alarm["max_price"] * 100
            log(f"[UST]   x {alarm['name']:<35} {best['price']:>18,}  (esik {alarm['max_price']:,}  %{pct:.0f})")

    unknown = {iid: cheapest[iid] for iid in cheapest if iid not in all_alarm_ids}
    if unknown:
        log(f"[UST]   [{len(unknown)} bilinmeyen ID ust pazarda goruldu]")
    if fired == 0: log("[UST]   -> Esik altinda alarm yok.")
    else:          log(f"[UST]   *** {fired} ALARM ATESLENEDI! ***")

def fire_alarm_ust(item_name, price, max_price):
    log(f"[UST] *** ALARM *** {item_name}  |  {price:,} gold")
    msg = (
        "AR MARKET - UST PAZAR ALARMI!\n\n"
        f"Item  : {item_name}\n"
        f"Fiyat : {price:,} gold\n"
        f"Esik  : {max_price:,} gold\n\n"
        "Hemen ust pazari ac!"
    )
    send_telegram(msg)

# ── UST PAZAR ARKA PLAN THREAD ────────────────────────────────────
_ust_lock = threading.Lock()

def ust_pazar_loop():
    """
    Ust pazar dinleme dongusu — arka plan thread'inde calisir.
    Port 19001'i surekli dinler. 15KB veri gelince analiz yapar.
    """
    tcpdump_bin = "/data/data/com.termux/files/usr/bin/tcpdump"
    log("[UST] Ust pazar dinleme baslatildi (port 19001).")

    while True:
        try:
            # Temizle ve baslat
            run_shell(f"su -c 'rm -f {PCAP_PATH_UST}'")
            proc = subprocess.Popen(
                f"su -c '{tcpdump_bin} -i any -s 0 tcp port {UST_PAZAR_PORT} -w {PCAP_PATH_UST}'",
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            time.sleep(2)

            # Veri birikimini bekle (15KB)
            while True:
                time.sleep(2)
                sz = get_pcap_size(PCAP_PATH_UST)
                if sz >= UST_BURST_BYTES:
                    log(f"[UST] Yeterli veri ({sz:,} byte). Analiz yapiliyor...")
                    break

            # Tcpdump'i durdur
            try: proc.kill()
            except: pass
            run_shell("su -c 'killall tcpdump 2>/dev/null'")
            time.sleep(1)

            # Pcap'i cek ve isle
            local_pcap = pull_pcap(PCAP_PATH_UST, "ar_ust_scan.pcap")
            if not local_pcap:
                log("[UST]   Pcap alinamadi.")
                time.sleep(5)
                continue

            pkts, link_type = read_packets(local_pcap)
            payload = extract_ust_payloads(pkts, link_type)
            log(f"[UST]   {len(pkts)} paket / {len(payload):,} byte veri")

            try: os.remove(local_pcap)
            except: pass

            if len(payload) == 0:
                log("[UST]   Veri bos veya sunucu filtresi gecmedi.")
            else:
                with _ust_lock:
                    recs = parse_ust_market(payload)
                    check_alarms_ust(recs)

            log("[UST] Ust pazar tekrar dinleniyor...")

        except Exception as e:
            log(f"[UST] Hata: {e}")
            time.sleep(5)

# ════════════════════════════════════════════
#  ANA DONGU
# ════════════════════════════════════════════

def main():
    log("=" * 60)
    log("  AR MARKET - PAZAR ALARM SISTEMI (Termux)")
    log("  Normal Pazar + Ust Pazar")
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
    send_telegram(f"AR Market Alarm baslatildi (v{VERSION}).\n{len(ALARM_LIST)} alarm aktif.\nNormal + Ust pazar dinleniyor.")
    log("")

    # Ust pazar thread olarak baslat
    ust_thread = threading.Thread(target=ust_pazar_loop, daemon=True)
    ust_thread.start()
    log("[UST] Arka plan thread baslatildi.")
    log("")

    # Normal pazar ana dongu
    scan_no           = 0
    tcpdump_proc      = None
    last_update_check = time.time()
    UPDATE_CHECK_INTERVAL = 60

    BURST_THRESHOLD = 15_000
    BURST_END_SECS  = 3

    try:
        while True:
            if tcpdump_proc is None or tcpdump_proc.poll() is not None:
                tcpdump_proc = start_tcpdump_normal()
                log("[NORMAL] Dinleniyor... Pazar persomenini ac.")

            prev_size     = get_pcap_size(PCAP_PATH)
            in_burst      = False
            burst_end_cnt = 0

            while True:
                time.sleep(1)

                if time.time() - last_update_check >= UPDATE_CHECK_INTERVAL:
                    last_update_check = time.time()
                    log("Guncelleme kontrol ediliyor...")
                    check_update()

                sz   = get_pcap_size(PCAP_PATH)
                diff = sz - prev_size
                prev_size = sz

                if diff >= BURST_THRESHOLD:
                    if not in_burst:
                        log(f"[NORMAL]   >>> Pazar verisi geliyor! ({diff//1024}KB/sn)")
                        in_burst = True
                    burst_end_cnt = 0
                elif in_burst:
                    burst_end_cnt += 1
                    if burst_end_cnt >= BURST_END_SECS:
                        log(f"[NORMAL]   Burst bitti, analiz basliyor...")
                        break
                else:
                    pass

            scan_no += 1
            log(f"\n[NORMAL] Tarama #{scan_no}")
            local_pcap = pull_pcap(PCAP_PATH, "ar_alarm_scan.pcap")
            if not local_pcap:
                log("[NORMAL]   Pcap alinamadi.")
                in_burst = False
                burst_end_cnt = 0
                continue

            pkts, link_type = read_packets(local_pcap)
            payload = extract_server_payloads(pkts, link_type)
            log(f"[NORMAL]   {len(pkts)} paket / {len(payload):,} byte server verisi")

            try: os.remove(local_pcap)
            except: pass

            if len(payload) == 0:
                log("[NORMAL]   Server verisi bos.")
            else:
                recs = parse_market_records(payload)
                check_alarms_normal(recs, pkts, link_type)

            log("[NORMAL]   30sn sonra persomeni tekrar ac.")
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
