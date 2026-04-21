import { Motherboard } from '../models/Motherboard';

function board(brand: string, chipset: string, model: string): Motherboard {
  const id = `${brand}::${chipset}::${model}`.toLowerCase().replace(/\s+/g, '_');
  return { id, brand, chipset, fullModelName: model };
}

export const STATIC_BOARDS: Motherboard[] = [
  // ── ASUS Intel Z890 ──
  board('ASUS', 'Z890', 'ROG MAXIMUS Z890 APEX'),
  board('ASUS', 'Z890', 'ROG STRIX Z890-E GAMING WIFI'),
  board('ASUS', 'Z890', 'TUF GAMING Z890-PLUS WIFI'),
  board('ASUS', 'Z890', 'PRIME Z890-P WIFI'),
  board('ASUS', 'Z890', 'ProArt Z890-CREATOR WIFI'),

  // ── ASUS Intel Z790 ──
  board('ASUS', 'Z790', 'ROG MAXIMUS Z790 HERO'),
  board('ASUS', 'Z790', 'ROG STRIX Z790-E GAMING WIFI'),
  board('ASUS', 'Z790', 'ROG STRIX Z790-F GAMING WIFI'),
  board('ASUS', 'Z790', 'ProArt Z790-CREATOR WIFI'),
  board('ASUS', 'Z790', 'TUF GAMING Z790-PLUS WIFI'),
  board('ASUS', 'Z790', 'PRIME Z790-P WIFI'),

  // ── ASUS Intel B860 ──
  board('ASUS', 'B860', 'TUF GAMING B860M-PLUS WIFI'),
  board('ASUS', 'B860', 'PRIME B860M-A WIFI'),

  // ── ASUS Intel B760 ──
  board('ASUS', 'B760', 'TUF GAMING B760-PLUS WIFI'),
  board('ASUS', 'B760', 'PRIME B760M-A WIFI'),
  board('ASUS', 'B760', 'PRIME B760-PLUS'),
  board('ASUS', 'B760', 'ROG STRIX B760-G GAMING WIFI'),

  // ── ASUS AMD X870E ──
  board('ASUS', 'X870E', 'ROG CROSSHAIR X870E HERO'),
  board('ASUS', 'X870E', 'ROG STRIX X870E-E GAMING WIFI'),
  board('ASUS', 'X870E', 'ProArt X870E-CREATOR WIFI'),

  // ── ASUS AMD X870 ──
  board('ASUS', 'X870', 'TUF GAMING X870-PLUS WIFI'),
  board('ASUS', 'X870', 'PRIME X870-P WIFI'),

  // ── ASUS AMD X670E ──
  board('ASUS', 'X670E', 'ROG CROSSHAIR X670E HERO'),
  board('ASUS', 'X670E', 'ROG CROSSHAIR X670E GENE'),
  board('ASUS', 'X670E', 'ROG STRIX X670E-E GAMING WIFI'),
  board('ASUS', 'X670E', 'ProArt X670E-CREATOR WIFI'),
  board('ASUS', 'X670E', 'TUF GAMING X670E-PLUS WIFI'),

  // ── ASUS AMD B650E ──
  board('ASUS', 'B650E', 'ROG STRIX B650E-F GAMING WIFI'),
  board('ASUS', 'B650E', 'ROG STRIX B650E-I GAMING WIFI'),
  board('ASUS', 'B650E', 'TUF GAMING B650E-PLUS WIFI'),

  // ── ASUS AMD B650 ──
  board('ASUS', 'B650', 'TUF GAMING B650-PLUS WIFI'),
  board('ASUS', 'B650', 'PRIME B650-PLUS'),
  board('ASUS', 'B650', 'PRIME B650M-A WIFI'),

  // ── GIGABYTE Intel Z890 ──
  board('GIGABYTE', 'Z890', 'Z890 AORUS MASTER'),
  board('GIGABYTE', 'Z890', 'Z890 AORUS ELITE X WIFI7'),
  board('GIGABYTE', 'Z890', 'Z890 GAMING X WIFI7'),
  board('GIGABYTE', 'Z890', 'Z890M AORUS ELITE WIFI7'),

  // ── GIGABYTE Intel Z790 ──
  board('GIGABYTE', 'Z790', 'Z790 AORUS MASTER'),
  board('GIGABYTE', 'Z790', 'Z790 AORUS ELITE AX'),
  board('GIGABYTE', 'Z790', 'Z790 GAMING X AX'),
  board('GIGABYTE', 'Z790', 'Z790M AORUS ELITE AX'),

  // ── GIGABYTE Intel B760 ──
  board('GIGABYTE', 'B760', 'B760 AORUS ELITE AX'),
  board('GIGABYTE', 'B760', 'B760M AORUS ELITE AX'),
  board('GIGABYTE', 'B760', 'B760M DS3H AX'),
  board('GIGABYTE', 'B760', 'B760 GAMING X AX'),

  // ── GIGABYTE AMD X870E ──
  board('GIGABYTE', 'X870E', 'X870E AORUS MASTER'),
  board('GIGABYTE', 'X870E', 'X870E AORUS XTREME AI TOP'),

  // ── GIGABYTE AMD X870 ──
  board('GIGABYTE', 'X870', 'X870 AORUS ELITE WIFI7'),
  board('GIGABYTE', 'X870', 'X870 GAMING X WIFI7'),

  // ── GIGABYTE AMD X670E ──
  board('GIGABYTE', 'X670E', 'X670E AORUS MASTER'),
  board('GIGABYTE', 'X670E', 'X670E AORUS XTREME'),
  board('GIGABYTE', 'X670E', 'X670E AORUS ELITE AX'),

  // ── GIGABYTE AMD B650 ──
  board('GIGABYTE', 'B650', 'B650 AORUS ELITE AX'),
  board('GIGABYTE', 'B650', 'B650M AORUS ELITE AX'),
  board('GIGABYTE', 'B650', 'B650M DS3H'),

  // ── MSI Intel Z890 ──
  board('MSI', 'Z890', 'MEG Z890 ACE'),
  board('MSI', 'Z890', 'MAG Z890 TOMAHAWK WIFI'),
  board('MSI', 'Z890', 'PRO Z890-A WIFI'),
  board('MSI', 'Z890', 'MPG Z890 CARBON WIFI'),

  // ── MSI Intel Z790 ──
  board('MSI', 'Z790', 'MEG Z790 ACE'),
  board('MSI', 'Z790', 'MEG Z790 GODLIKE'),
  board('MSI', 'Z790', 'MAG Z790 TOMAHAWK WIFI'),
  board('MSI', 'Z790', 'MAG Z790 TOMAHAWK MAX WIFI'),
  board('MSI', 'Z790', 'PRO Z790-A WIFI'),
  board('MSI', 'Z790', 'MPG Z790 CARBON WIFI'),

  // ── MSI Intel B760 ──
  board('MSI', 'B760', 'MAG B760 TOMAHAWK WIFI'),
  board('MSI', 'B760', 'PRO B760-P WIFI'),
  board('MSI', 'B760', 'PRO B760M-A WIFI'),

  // ── MSI AMD X870E ──
  board('MSI', 'X870E', 'MEG X870E ACE'),
  board('MSI', 'X870E', 'MEG X870E GODLIKE'),
  board('MSI', 'X870E', 'MPG X870E CARBON WIFI'),

  // ── MSI AMD X870 ──
  board('MSI', 'X870', 'MAG X870 TOMAHAWK WIFI'),
  board('MSI', 'X870', 'PRO X870-P WIFI'),

  // ── MSI AMD X670E ──
  board('MSI', 'X670E', 'MEG X670E ACE'),
  board('MSI', 'X670E', 'MEG X670E GODLIKE'),
  board('MSI', 'X670E', 'MPG X670E CARBON WIFI'),

  // ── MSI AMD B650 ──
  board('MSI', 'B650', 'MAG B650 TOMAHAWK WIFI'),
  board('MSI', 'B650', 'PRO B650-P WIFI'),
  board('MSI', 'B650', 'MAG B650M MORTAR WIFI'),

  // ── ASRock Intel Z890 ──
  board('ASRock', 'Z890', 'Z890 Taichi'),
  board('ASRock', 'Z890', 'Z890 Nova WiFi'),
  board('ASRock', 'Z890', 'Z890 Steel Legend WiFi'),
  board('ASRock', 'Z890', 'Z890 Pro RS WiFi'),

  // ── ASRock Intel Z790 ──
  board('ASRock', 'Z790', 'Z790 Taichi'),
  board('ASRock', 'Z790', 'Z790 Taichi Carrara'),
  board('ASRock', 'Z790', 'Z790 Steel Legend WiFi'),
  board('ASRock', 'Z790', 'Z790 PG Sonic'),
  board('ASRock', 'Z790', 'Z790 Pro RS WiFi'),

  // ── ASRock Intel B760 ──
  board('ASRock', 'B760', 'B760M Steel Legend WiFi'),
  board('ASRock', 'B760', 'B760 Steel Legend WiFi'),
  board('ASRock', 'B760', 'B760M Pro RS/D4'),

  // ── ASRock AMD X870E ──
  board('ASRock', 'X870E', 'X870E Taichi'),
  board('ASRock', 'X870E', 'X870E Nova WiFi'),
  board('ASRock', 'X870E', 'X870E Steel Legend WiFi'),

  // ── ASRock AMD X870 ──
  board('ASRock', 'X870', 'X870 Steel Legend WiFi'),
  board('ASRock', 'X870', 'X870 Pro RS WiFi'),

  // ── ASRock AMD X670E ──
  board('ASRock', 'X670E', 'X670E Taichi'),
  board('ASRock', 'X670E', 'X670E Steel Legend'),
  board('ASRock', 'X670E', 'X670E PG Lightning'),

  // ── ASRock AMD B650 ──
  board('ASRock', 'B650', 'B650 Steel Legend WiFi'),
  board('ASRock', 'B650', 'B650M Steel Legend'),
  board('ASRock', 'B650', 'B650E Steel Legend WiFi'),
];
