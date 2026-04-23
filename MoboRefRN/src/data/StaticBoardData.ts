import { Motherboard } from '../models/Motherboard';

function board(brand: string, chipset: string, model: string): Motherboard {
  const id = `${brand}::${chipset}::${model}`.toLowerCase().replace(/\s+/g, '_');
  return { id, brand, chipset, fullModelName: model };
}

export const STATIC_BOARDS: Motherboard[] = [

  // ════════════════════════════════════════
  // DDR5 — Intel Arrow Lake (Z890 / B860)
  // ════════════════════════════════════════

  board('ASUS', 'Z890', 'ROG MAXIMUS Z890 APEX'),
  board('ASUS', 'Z890', 'ROG STRIX Z890-E GAMING WIFI'),
  board('ASUS', 'Z890', 'TUF GAMING Z890-PLUS WIFI'),
  board('ASUS', 'Z890', 'PRIME Z890-P WIFI'),
  board('ASUS', 'Z890', 'ProArt Z890-CREATOR WIFI'),
  board('ASUS', 'B860', 'TUF GAMING B860M-PLUS WIFI'),
  board('ASUS', 'B860', 'PRIME B860M-A WIFI'),

  board('GIGABYTE', 'Z890', 'Z890 AORUS MASTER'),
  board('GIGABYTE', 'Z890', 'Z890 AORUS ELITE X WIFI7'),
  board('GIGABYTE', 'Z890', 'Z890 GAMING X WIFI7'),
  board('GIGABYTE', 'Z890', 'Z890M AORUS ELITE WIFI7'),

  board('MSI', 'Z890', 'MEG Z890 ACE'),
  board('MSI', 'Z890', 'MAG Z890 TOMAHAWK WIFI'),
  board('MSI', 'Z890', 'PRO Z890-A WIFI'),
  board('MSI', 'Z890', 'MPG Z890 CARBON WIFI'),

  board('ASRock', 'Z890', 'Z890 Taichi'),
  board('ASRock', 'Z890', 'Z890 Nova WiFi'),
  board('ASRock', 'Z890', 'Z890 Steel Legend WiFi'),
  board('ASRock', 'Z890', 'Z890 Pro RS WiFi'),

  // ════════════════════════════════════════
  // DDR5 — Intel Raptor Lake (13th/14th Gen) Z790 / B760
  // ════════════════════════════════════════

  board('ASUS', 'Z790', 'ROG MAXIMUS Z790 HERO'),
  board('ASUS', 'Z790', 'ROG MAXIMUS Z790 APEX'),
  board('ASUS', 'Z790', 'ROG STRIX Z790-E GAMING WIFI'),
  board('ASUS', 'Z790', 'ROG STRIX Z790-F GAMING WIFI'),
  board('ASUS', 'Z790', 'ProArt Z790-CREATOR WIFI'),
  board('ASUS', 'Z790', 'TUF GAMING Z790-PLUS WIFI'),
  board('ASUS', 'Z790', 'PRIME Z790-P WIFI'),
  board('ASUS', 'B760', 'TUF GAMING B760-PLUS WIFI'),
  board('ASUS', 'B760', 'TUF GAMING B760M-PLUS WIFI D4'),
  board('ASUS', 'B760', 'PRIME B760M-A WIFI'),
  board('ASUS', 'B760', 'PRIME B760-PLUS'),
  board('ASUS', 'B760', 'ROG STRIX B760-G GAMING WIFI'),

  board('GIGABYTE', 'Z790', 'Z790 AORUS MASTER'),
  board('GIGABYTE', 'Z790', 'Z790 AORUS ELITE AX'),
  board('GIGABYTE', 'Z790', 'Z790 GAMING X AX'),
  board('GIGABYTE', 'Z790', 'Z790M AORUS ELITE AX'),
  board('GIGABYTE', 'B760', 'B760 AORUS ELITE AX'),
  board('GIGABYTE', 'B760', 'B760M AORUS ELITE AX'),
  board('GIGABYTE', 'B760', 'B760M DS3H AX'),
  board('GIGABYTE', 'B760', 'B760 GAMING X AX'),

  board('MSI', 'Z790', 'MEG Z790 ACE'),
  board('MSI', 'Z790', 'MEG Z790 GODLIKE'),
  board('MSI', 'Z790', 'MAG Z790 TOMAHAWK WIFI'),
  board('MSI', 'Z790', 'MAG Z790 TOMAHAWK MAX WIFI'),
  board('MSI', 'Z790', 'PRO Z790-A WIFI'),
  board('MSI', 'Z790', 'MPG Z790 CARBON WIFI'),
  board('MSI', 'B760', 'MAG B760 TOMAHAWK WIFI'),
  board('MSI', 'B760', 'PRO B760-P WIFI'),
  board('MSI', 'B760', 'PRO B760M-A WIFI'),

  board('ASRock', 'Z790', 'Z790 Taichi'),
  board('ASRock', 'Z790', 'Z790 Taichi Carrara'),
  board('ASRock', 'Z790', 'Z790 Steel Legend WiFi'),
  board('ASRock', 'Z790', 'Z790 PG Sonic'),
  board('ASRock', 'Z790', 'Z790 Pro RS WiFi'),
  board('ASRock', 'B760', 'B760M Steel Legend WiFi'),
  board('ASRock', 'B760', 'B760 Steel Legend WiFi'),
  board('ASRock', 'B760', 'B760M Pro RS/D4'),

  // ════════════════════════════════════════
  // DDR5 — AMD Zen 5 (X870E / X870)
  // ════════════════════════════════════════

  board('ASUS', 'X870E', 'ROG CROSSHAIR X870E HERO'),
  board('ASUS', 'X870E', 'ROG STRIX X870E-E GAMING WIFI'),
  board('ASUS', 'X870E', 'ProArt X870E-CREATOR WIFI'),
  board('ASUS', 'X870', 'TUF GAMING X870-PLUS WIFI'),
  board('ASUS', 'X870', 'PRIME X870-P WIFI'),

  board('GIGABYTE', 'X870E', 'X870E AORUS MASTER'),
  board('GIGABYTE', 'X870E', 'X870E AORUS XTREME AI TOP'),
  board('GIGABYTE', 'X870', 'X870 AORUS ELITE WIFI7'),
  board('GIGABYTE', 'X870', 'X870 GAMING X WIFI7'),

  board('MSI', 'X870E', 'MEG X870E ACE'),
  board('MSI', 'X870E', 'MEG X870E GODLIKE'),
  board('MSI', 'X870E', 'MPG X870E CARBON WIFI'),
  board('MSI', 'X870', 'MAG X870 TOMAHAWK WIFI'),
  board('MSI', 'X870', 'PRO X870-P WIFI'),

  board('ASRock', 'X870E', 'X870E Taichi'),
  board('ASRock', 'X870E', 'X870E Nova WiFi'),
  board('ASRock', 'X870E', 'X870E Steel Legend WiFi'),
  board('ASRock', 'X870', 'X870 Steel Legend WiFi'),
  board('ASRock', 'X870', 'X870 Pro RS WiFi'),

  // ════════════════════════════════════════
  // DDR5 — AMD Zen 4 (X670E / X670 / B650E / B650)
  // ════════════════════════════════════════

  board('ASUS', 'X670E', 'ROG CROSSHAIR X670E HERO'),
  board('ASUS', 'X670E', 'ROG CROSSHAIR X670E GENE'),
  board('ASUS', 'X670E', 'ROG STRIX X670E-E GAMING WIFI'),
  board('ASUS', 'X670E', 'ProArt X670E-CREATOR WIFI'),
  board('ASUS', 'X670E', 'TUF GAMING X670E-PLUS WIFI'),
  board('ASUS', 'B650E', 'ROG STRIX B650E-F GAMING WIFI'),
  board('ASUS', 'B650E', 'ROG STRIX B650E-I GAMING WIFI'),
  board('ASUS', 'B650E', 'TUF GAMING B650E-PLUS WIFI'),
  board('ASUS', 'B650', 'TUF GAMING B650-PLUS WIFI'),
  board('ASUS', 'B650', 'PRIME B650-PLUS'),
  board('ASUS', 'B650', 'PRIME B650M-A WIFI'),

  board('GIGABYTE', 'X670E', 'X670E AORUS MASTER'),
  board('GIGABYTE', 'X670E', 'X670E AORUS XTREME'),
  board('GIGABYTE', 'X670E', 'X670E AORUS ELITE AX'),
  board('GIGABYTE', 'B650', 'B650 AORUS ELITE AX'),
  board('GIGABYTE', 'B650', 'B650M AORUS ELITE AX'),
  board('GIGABYTE', 'B650', 'B650M DS3H'),
  board('GIGABYTE', 'B650', 'B650M C V3 (rev. 1.0)'),
  board('GIGABYTE', 'B650', 'B650 GAMING X AX V2'),

  board('MSI', 'X670E', 'MEG X670E ACE'),
  board('MSI', 'X670E', 'MEG X670E GODLIKE'),
  board('MSI', 'X670E', 'MPG X670E CARBON WIFI'),
  board('MSI', 'B650', 'MAG B650 TOMAHAWK WIFI'),
  board('MSI', 'B650', 'PRO B650-P WIFI'),
  board('MSI', 'B650', 'MAG B650M MORTAR WIFI'),
  board('MSI', 'B650', 'PRO B650M-A WIFI'),

  board('ASRock', 'X670E', 'X670E Taichi'),
  board('ASRock', 'X670E', 'X670E Steel Legend'),
  board('ASRock', 'X670E', 'X670E PG Lightning'),
  board('ASRock', 'B650', 'B650 Steel Legend WiFi'),
  board('ASRock', 'B650', 'B650M Steel Legend'),
  board('ASRock', 'B650', 'B650E Steel Legend WiFi'),
  board('ASRock', 'B650', 'B650M Pro RS WiFi'),

  // ════════════════════════════════════════
  // DDR4 — Intel Alder Lake (12th Gen) Z690 / B660 / H610
  // ════════════════════════════════════════

  board('ASUS', 'Z690', 'ROG MAXIMUS Z690 HERO'),
  board('ASUS', 'Z690', 'ROG MAXIMUS Z690 APEX'),
  board('ASUS', 'Z690', 'ROG STRIX Z690-E GAMING WIFI'),
  board('ASUS', 'Z690', 'TUF GAMING Z690-PLUS WIFI D4'),
  board('ASUS', 'Z690', 'PRIME Z690-P D4'),
  board('ASUS', 'Z690', 'ProArt Z690-CREATOR WIFI'),
  board('ASUS', 'B660', 'TUF GAMING B660M-PLUS WIFI D4'),
  board('ASUS', 'B660', 'PRIME B660M-A D4'),
  board('ASUS', 'B660', 'ROG STRIX B660-G GAMING WIFI'),
  board('ASUS', 'B660', 'PRIME B660-PLUS D4'),
  board('ASUS', 'H610', 'PRIME H610M-E D4'),
  board('ASUS', 'H610', 'PRIME H610M-K D4'),

  board('GIGABYTE', 'Z690', 'Z690 AORUS MASTER'),
  board('GIGABYTE', 'Z690', 'Z690 AORUS ELITE AX DDR4'),
  board('GIGABYTE', 'Z690', 'Z690 GAMING X DDR4'),
  board('GIGABYTE', 'Z690', 'Z690M AORUS ELITE AX DDR4'),
  board('GIGABYTE', 'Z690', 'Z690 UD DDR4'),
  board('GIGABYTE', 'B660', 'B660 AORUS MASTER DDR4'),
  board('GIGABYTE', 'B660', 'B660M AORUS PRO AX DDR4'),
  board('GIGABYTE', 'B660', 'B660M DS3H AX DDR4'),
  board('GIGABYTE', 'B660', 'B660 GAMING X DDR4'),
  board('GIGABYTE', 'H610', 'H610M S2H DDR4'),
  board('GIGABYTE', 'H610', 'H610M H DDR4'),

  board('MSI', 'Z690', 'MEG Z690 ACE'),
  board('MSI', 'Z690', 'MEG Z690 GODLIKE'),
  board('MSI', 'Z690', 'MAG Z690 TOMAHAWK WIFI DDR4'),
  board('MSI', 'Z690', 'PRO Z690-A WIFI DDR4'),
  board('MSI', 'Z690', 'MPG Z690 CARBON WIFI DDR4'),
  board('MSI', 'B660', 'MAG B660 TOMAHAWK WIFI DDR4'),
  board('MSI', 'B660', 'PRO B660M-A WIFI DDR4'),
  board('MSI', 'B660', 'PRO B660-A DDR4'),
  board('MSI', 'H610', 'PRO H610M-E DDR4'),
  board('MSI', 'H610', 'PRO H610M-G DDR4'),

  board('ASRock', 'Z690', 'Z690 Taichi'),
  board('ASRock', 'Z690', 'Z690 Steel Legend WiFi 6E'),
  board('ASRock', 'Z690', 'Z690 Pro RS D4'),
  board('ASRock', 'Z690', 'Z690 Phantom Gaming 4 D4'),
  board('ASRock', 'B660', 'B660M Steel Legend WiFi'),
  board('ASRock', 'B660', 'B660 Steel Legend WiFi 6E'),
  board('ASRock', 'B660', 'B660M Pro RS D4'),
  board('ASRock', 'H610', 'H610M-HDV/M.2'),
  board('ASRock', 'H610', 'H610M-ITX/ac'),

  // ════════════════════════════════════════
  // DDR4 — Intel Rocket Lake (11th Gen) Z590 / B560 / H510
  // ════════════════════════════════════════

  board('ASUS', 'Z590', 'ROG MAXIMUS XIII HERO'),
  board('ASUS', 'Z590', 'ROG STRIX Z590-E GAMING WIFI'),
  board('ASUS', 'Z590', 'TUF GAMING Z590-PLUS WIFI'),
  board('ASUS', 'Z590', 'PRIME Z590-A'),
  board('ASUS', 'B560', 'TUF GAMING B560M-PLUS WIFI'),
  board('ASUS', 'B560', 'PRIME B560M-A'),
  board('ASUS', 'B560', 'ROG STRIX B560-F GAMING WIFI'),
  board('ASUS', 'B560', 'PRIME B560-PLUS'),
  board('ASUS', 'H510', 'PRIME H510M-E'),
  board('ASUS', 'H510', 'PRIME H510M-K'),

  board('GIGABYTE', 'Z590', 'Z590 AORUS MASTER'),
  board('GIGABYTE', 'Z590', 'Z590 AORUS XTREME'),
  board('GIGABYTE', 'Z590', 'Z590 GAMING X'),
  board('GIGABYTE', 'Z590', 'Z590M GAMING X'),
  board('GIGABYTE', 'B560', 'B560 AORUS PRO AX'),
  board('GIGABYTE', 'B560', 'B560M AORUS PRO AX'),
  board('GIGABYTE', 'B560', 'B560M DS3H'),

  board('MSI', 'Z590', 'MEG Z590 ACE'),
  board('MSI', 'Z590', 'MAG Z590 TOMAHAWK WIFI'),
  board('MSI', 'Z590', 'MPG Z590 GAMING CARBON WIFI'),
  board('MSI', 'Z590', 'PRO Z590-A'),
  board('MSI', 'B560', 'MAG B560 TOMAHAWK WIFI'),
  board('MSI', 'B560', 'PRO B560M-A AC'),
  board('MSI', 'B560', 'PRO B560-A AC'),

  board('ASRock', 'Z590', 'Z590 Taichi'),
  board('ASRock', 'Z590', 'Z590 Steel Legend WiFi 6E'),
  board('ASRock', 'Z590', 'Z590 Pro4'),
  board('ASRock', 'B560', 'B560M Steel Legend'),
  board('ASRock', 'B560', 'B560 Steel Legend WiFi 6E'),
  board('ASRock', 'B560', 'B560M Pro4'),

  // ════════════════════════════════════════
  // DDR4 — Intel Comet Lake (10th Gen) Z490 / B460 / H470
  // ════════════════════════════════════════

  board('ASUS', 'Z490', 'ROG MAXIMUS XII HERO (WIFI)'),
  board('ASUS', 'Z490', 'ROG STRIX Z490-E GAMING'),
  board('ASUS', 'Z490', 'TUF GAMING Z490-PLUS (WIFI)'),
  board('ASUS', 'Z490', 'PRIME Z490-A'),
  board('ASUS', 'B460', 'TUF GAMING B460M-PLUS (WIFI)'),
  board('ASUS', 'B460', 'PRIME B460M-A'),
  board('ASUS', 'H470', 'TUF GAMING H470-PRO (WIFI)'),
  board('ASUS', 'H470', 'PRIME H470M-PLUS'),

  board('GIGABYTE', 'Z490', 'Z490 AORUS MASTER'),
  board('GIGABYTE', 'Z490', 'Z490 AORUS ULTRA'),
  board('GIGABYTE', 'Z490', 'Z490 GAMING X AX'),
  board('GIGABYTE', 'Z490', 'Z490M GAMING X'),
  board('GIGABYTE', 'B460', 'B460M AORUS PRO'),
  board('GIGABYTE', 'B460', 'B460 AORUS PRO AX'),
  board('GIGABYTE', 'B460', 'B460M DS3H'),

  board('MSI', 'Z490', 'MEG Z490 ACE'),
  board('MSI', 'Z490', 'MAG Z490 TOMAHAWK'),
  board('MSI', 'Z490', 'MPG Z490 GAMING CARBON WIFI'),
  board('MSI', 'B460', 'MAG B460 TOMAHAWK'),
  board('MSI', 'B460', 'PRO B460M-A AC'),

  board('ASRock', 'Z490', 'Z490 Taichi'),
  board('ASRock', 'Z490', 'Z490 Steel Legend WiFi 6'),
  board('ASRock', 'Z490', 'Z490 Pro4'),
  board('ASRock', 'B460', 'B460M Steel Legend'),
  board('ASRock', 'B460', 'B460M Pro4'),

  // ════════════════════════════════════════
  // DDR4 — AMD Zen 3 / Zen 2 (X570 / B550 / A520)
  // ════════════════════════════════════════

  board('ASUS', 'X570', 'ROG CROSSHAIR VIII HERO (WIFI)'),
  board('ASUS', 'X570', 'ROG CROSSHAIR VIII DARK HERO'),
  board('ASUS', 'X570', 'ROG STRIX X570-E GAMING WIFI II'),
  board('ASUS', 'X570', 'ROG STRIX X570-F GAMING'),
  board('ASUS', 'X570', 'TUF GAMING X570-PLUS (WIFI)'),
  board('ASUS', 'X570', 'PRIME X570-PRO'),
  board('ASUS', 'X570', 'ProArt X570-CREATOR WIFI'),
  board('ASUS', 'B550', 'ROG STRIX B550-F GAMING (WIFI II)'),
  board('ASUS', 'B550', 'ROG STRIX B550-I GAMING'),
  board('ASUS', 'B550', 'ROG STRIX B550-A GAMING'),
  board('ASUS', 'B550', 'TUF GAMING B550-PLUS WIFI II'),
  board('ASUS', 'B550', 'TUF GAMING B550M-PLUS WIFI II'),
  board('ASUS', 'B550', 'PRIME B550M-A (WIFI)'),
  board('ASUS', 'B550', 'PRIME B550-PLUS'),
  board('ASUS', 'A520', 'PRIME A520M-E'),
  board('ASUS', 'A520', 'PRIME A520M-K'),
  board('ASUS', 'A520', 'TUF GAMING A520M-PLUS WIFI'),

  board('GIGABYTE', 'X570', 'X570 AORUS MASTER'),
  board('GIGABYTE', 'X570', 'X570 AORUS XTREME'),
  board('GIGABYTE', 'X570', 'X570 AORUS PRO WIFI'),
  board('GIGABYTE', 'X570', 'X570S AORUS MASTER'),
  board('GIGABYTE', 'X570', 'X570 GAMING X'),
  board('GIGABYTE', 'X570', 'X570M AORUS PRO'),
  board('GIGABYTE', 'B550', 'B550 AORUS MASTER'),
  board('GIGABYTE', 'B550', 'B550 AORUS PRO AX'),
  board('GIGABYTE', 'B550', 'B550 AORUS ELITE V2'),
  board('GIGABYTE', 'B550', 'B550M AORUS PRO-P'),
  board('GIGABYTE', 'B550', 'B550M DS3H AC'),
  board('GIGABYTE', 'B550', 'B550 GAMING X V2'),
  board('GIGABYTE', 'A520', 'A520M AORUS ELITE'),
  board('GIGABYTE', 'A520', 'A520M DS3H'),
  board('GIGABYTE', 'A520', 'A520M S2H'),

  board('MSI', 'X570', 'MEG X570 ACE'),
  board('MSI', 'X570', 'MEG X570 GODLIKE'),
  board('MSI', 'X570', 'MAG X570S TOMAHAWK MAX WIFI'),
  board('MSI', 'X570', 'MPG X570 GAMING EDGE WIFI'),
  board('MSI', 'X570', 'MPG X570 GAMING PLUS'),
  board('MSI', 'B550', 'MAG B550 TOMAHAWK'),
  board('MSI', 'B550', 'MAG B550M MORTAR WIFI'),
  board('MSI', 'B550', 'MAG B550M MORTAR MAX WIFI'),
  board('MSI', 'B550', 'MPG B550 GAMING EDGE WIFI'),
  board('MSI', 'B550', 'PRO B550-VC'),
  board('MSI', 'B550', 'PRO B550M-VC WIFI'),
  board('MSI', 'A520', 'PRO A520M-A PRO'),
  board('MSI', 'A520', 'PRO A520M GRAND'),

  board('ASRock', 'X570', 'X570 Taichi'),
  board('ASRock', 'X570', 'X570 Taichi Razer Edition'),
  board('ASRock', 'X570', 'X570 Steel Legend WiFi ax'),
  board('ASRock', 'X570', 'X570 Pro4'),
  board('ASRock', 'X570', 'X570M Pro4'),
  board('ASRock', 'B550', 'B550 Taichi'),
  board('ASRock', 'B550', 'B550 Steel Legend'),
  board('ASRock', 'B550', 'B550M Steel Legend'),
  board('ASRock', 'B550', 'B550 Pro4'),
  board('ASRock', 'B550', 'B550M Pro4'),
  board('ASRock', 'B550', 'B550M-HDV'),
  board('ASRock', 'A520', 'A520M-HDV'),
  board('ASRock', 'A520', 'A520M Pro4'),
  board('ASRock', 'A520', 'A520M-ITX/ac'),

  // ════════════════════════════════════════
  // DDR4 — AMD Zen 2 / Zen+ (X470 / B450 / A320)
  // ════════════════════════════════════════

  board('ASUS', 'X470', 'ROG CROSSHAIR VII HERO (WIFI)'),
  board('ASUS', 'X470', 'ROG STRIX X470-F GAMING'),
  board('ASUS', 'X470', 'TUF X470-PLUS GAMING'),
  board('ASUS', 'X470', 'PRIME X470-PRO'),
  board('ASUS', 'B450', 'ROG STRIX B450-F GAMING II'),
  board('ASUS', 'B450', 'ROG STRIX B450-I GAMING'),
  board('ASUS', 'B450', 'TUF GAMING B450M-PRO S'),
  board('ASUS', 'B450', 'TUF GAMING B450-PLUS II'),
  board('ASUS', 'B450', 'PRIME B450M-A II'),
  board('ASUS', 'B450', 'PRIME B450M-K II'),
  board('ASUS', 'B450', 'PRIME B450-PLUS'),
  board('ASUS', 'A320', 'PRIME A320M-K'),
  board('ASUS', 'A320', 'PRIME A320M-E'),

  board('GIGABYTE', 'X470', 'X470 AORUS GAMING 7 WIFI'),
  board('GIGABYTE', 'X470', 'X470 AORUS ULTRA GAMING'),
  board('GIGABYTE', 'X470', 'X470 AORUS GAMING 5 WIFI'),
  board('GIGABYTE', 'B450', 'B450 AORUS PRO WIFI'),
  board('GIGABYTE', 'B450', 'B450 AORUS M'),
  board('GIGABYTE', 'B450', 'B450M DS3H V2'),
  board('GIGABYTE', 'B450', 'B450M DS3H WIFI'),
  board('GIGABYTE', 'B450', 'B450 GAMING X'),
  board('GIGABYTE', 'A320', 'GA-A320M-S2H'),
  board('GIGABYTE', 'A320', 'GA-A320M-H'),

  board('MSI', 'X470', 'MEG X470 GAMING PRO CARBON'),
  board('MSI', 'X470', 'X470 GAMING PLUS MAX'),
  board('MSI', 'X470', 'X470 GAMING PRO MAX'),
  board('MSI', 'B450', 'MAG B450 TOMAHAWK MAX'),
  board('MSI', 'B450', 'MAG B450M MORTAR MAX'),
  board('MSI', 'B450', 'B450M PRO-VDH MAX'),
  board('MSI', 'B450', 'B450-A PRO MAX'),
  board('MSI', 'B450', 'B450M GAMING PLUS'),
  board('MSI', 'A320', 'A320M PRO-VH PLUS'),
  board('MSI', 'A320', 'A320M-A PRO MAX'),

  board('ASRock', 'X470', 'X470 Taichi'),
  board('ASRock', 'X470', 'X470 Master SLI/ac'),
  board('ASRock', 'X470', 'Fatal1ty X470 Gaming K4'),
  board('ASRock', 'B450', 'B450 Steel Legend'),
  board('ASRock', 'B450', 'B450M Steel Legend'),
  board('ASRock', 'B450', 'B450 Pro4'),
  board('ASRock', 'B450', 'B450M Pro4'),
  board('ASRock', 'B450', 'B450M-HDV R4.0'),
  board('ASRock', 'B450', 'Fatal1ty B450 Gaming K4'),
  board('ASRock', 'A320', 'A320M-HDV R4.0'),
  board('ASRock', 'A320', 'A320M Pro4'),

  // ════════════════════════════════════════
  // DDR4 — Intel Coffee Lake Refresh (9th Gen) Z390 / B365 / H370
  // ════════════════════════════════════════

  board('ASUS', 'Z390', 'ROG MAXIMUS XI HERO (WIFI)'),
  board('ASUS', 'Z390', 'ROG MAXIMUS XI APEX'),
  board('ASUS', 'Z390', 'ROG STRIX Z390-E GAMING'),
  board('ASUS', 'Z390', 'ROG STRIX Z390-F GAMING'),
  board('ASUS', 'Z390', 'TUF Z390-PLUS GAMING (WIFI)'),
  board('ASUS', 'Z390', 'PRIME Z390-A'),
  board('ASUS', 'Z390', 'PRIME Z390-P'),
  board('ASUS', 'B365', 'PRIME B365M-A'),
  board('ASUS', 'B365', 'PRIME B365-PLUS'),
  board('ASUS', 'B365', 'TUF B365M-PLUS GAMING'),
  board('ASUS', 'H370', 'ROG STRIX H370-F GAMING'),
  board('ASUS', 'H370', 'TUF H370-PRO GAMING (WIFI)'),
  board('ASUS', 'H370', 'PRIME H370M-PLUS'),

  board('GIGABYTE', 'Z390', 'Z390 AORUS MASTER'),
  board('GIGABYTE', 'Z390', 'Z390 AORUS XTREME'),
  board('GIGABYTE', 'Z390', 'Z390 AORUS PRO WIFI'),
  board('GIGABYTE', 'Z390', 'Z390 AORUS ELITE'),
  board('GIGABYTE', 'Z390', 'Z390 GAMING X'),
  board('GIGABYTE', 'Z390', 'Z390M GAMING'),
  board('GIGABYTE', 'B365', 'B365M DS3H'),
  board('GIGABYTE', 'B365', 'B365M AORUS ELITE'),
  board('GIGABYTE', 'H370', 'H370M D3H GSM'),
  board('GIGABYTE', 'H370', 'H370 AORUS GAMING 3 WIFI'),

  board('MSI', 'Z390', 'MEG Z390 ACE'),
  board('MSI', 'Z390', 'MEG Z390 GODLIKE'),
  board('MSI', 'Z390', 'MPG Z390 GAMING PRO CARBON AC'),
  board('MSI', 'Z390', 'MAG Z390 TOMAHAWK'),
  board('MSI', 'Z390', 'Z390-A PRO'),
  board('MSI', 'B365', 'B365M PRO-A'),
  board('MSI', 'B365', 'B365M PRO-VD PLUS'),
  board('MSI', 'H370', 'H370 GAMING PRO CARBON'),
  board('MSI', 'H370', 'H370M BAZOOKA'),

  board('ASRock', 'Z390', 'Z390 Taichi'),
  board('ASRock', 'Z390', 'Z390 Taichi Ultimate'),
  board('ASRock', 'Z390', 'Z390 Phantom Gaming 9'),
  board('ASRock', 'Z390', 'Z390 Steel Legend'),
  board('ASRock', 'Z390', 'Z390 Pro4'),
  board('ASRock', 'B365', 'B365M Phantom Gaming 4'),
  board('ASRock', 'B365', 'B365M Pro4'),
  board('ASRock', 'H370', 'H370M-ITX/ac'),
  board('ASRock', 'H370', 'H370 Performance'),

  // ════════════════════════════════════════
  // DDR4 — Intel Coffee Lake (8th Gen) Z370 / B360 / H310
  // ════════════════════════════════════════

  board('ASUS', 'Z370', 'ROG MAXIMUS X HERO'),
  board('ASUS', 'Z370', 'ROG MAXIMUS X APEX'),
  board('ASUS', 'Z370', 'ROG STRIX Z370-E GAMING'),
  board('ASUS', 'Z370', 'ROG STRIX Z370-F GAMING'),
  board('ASUS', 'Z370', 'TUF Z370-PLUS GAMING'),
  board('ASUS', 'Z370', 'PRIME Z370-A'),
  board('ASUS', 'Z370', 'PRIME Z370-P'),
  board('ASUS', 'B360', 'PRIME B360M-A'),
  board('ASUS', 'B360', 'TUF B360-PRO GAMING (WIFI)'),
  board('ASUS', 'H310', 'PRIME H310M-E R2.0'),
  board('ASUS', 'H310', 'PRIME H310M-K R2.0'),

  board('GIGABYTE', 'Z370', 'Z370 AORUS Gaming 7'),
  board('GIGABYTE', 'Z370', 'Z370 AORUS Gaming 5'),
  board('GIGABYTE', 'Z370', 'Z370 AORUS Ultra Gaming'),
  board('GIGABYTE', 'Z370', 'Z370 HD3'),
  board('GIGABYTE', 'Z370', 'Z370M DS3H'),
  board('GIGABYTE', 'B360', 'B360M AORUS Gaming 3'),
  board('GIGABYTE', 'B360', 'B360M DS3H'),
  board('GIGABYTE', 'H310', 'H310M S2H 2.0'),
  board('GIGABYTE', 'H310', 'H310M M.2 2.0'),

  board('MSI', 'Z370', 'MEG Z370 GODLIKE GAMING'),
  board('MSI', 'Z370', 'Z370 GAMING PRO CARBON'),
  board('MSI', 'Z370', 'Z370 GAMING PLUS'),
  board('MSI', 'Z370', 'Z370-A PRO'),
  board('MSI', 'B360', 'B360M GAMING PLUS'),
  board('MSI', 'B360', 'B360M PRO-VDH'),
  board('MSI', 'H310', 'H310M PRO-VDH PLUS'),
  board('MSI', 'H310', 'H310M PRO-M2 PLUS'),

  board('ASRock', 'Z370', 'Z370 Taichi'),
  board('ASRock', 'Z370', 'Z370 Killer SLI/ac'),
  board('ASRock', 'Z370', 'Z370 Extreme4'),
  board('ASRock', 'Z370', 'Z370 Pro4'),
  board('ASRock', 'B360', 'B360M Pro4'),
  board('ASRock', 'B360', 'B360M-ITX/ac'),
  board('ASRock', 'H310', 'H310M-HDV/M.2'),
  board('ASRock', 'H310', 'H310CM-DVS'),

  // ════════════════════════════════════════
  // DDR5 — Additional B650 / B650E variants
  // ════════════════════════════════════════

  board('ASUS', 'B650', 'ROG STRIX B650-A GAMING WIFI'),
  board('ASUS', 'B650', 'ProArt B650-CREATOR'),
  board('ASUS', 'B650E', 'ProArt B650E-CREATOR WIFI'),

  board('GIGABYTE', 'B650', 'B650 AORUS PRO AX'),
  board('GIGABYTE', 'B650', 'B650M AORUS PRO'),
  board('GIGABYTE', 'B650', 'B650M AORUS ELITE'),
  board('GIGABYTE', 'B650E', 'B650E AORUS MASTER'),
  board('GIGABYTE', 'B650E', 'B650E AORUS PRO X'),

  board('MSI', 'B650E', 'MPG B650E CARBON WIFI'),
  board('MSI', 'B650E', 'MEG B650E UNIFY'),

  board('ASRock', 'B650', 'B650 LiveMixer'),
  board('ASRock', 'B650', 'B650M-C'),
  board('ASRock', 'B650E', 'B650E PG Riptide WiFi'),

  // ════════════════════════════════════════
  // DDR5 — Additional B760 / Z790 variants
  // ════════════════════════════════════════

  board('ASUS', 'B760', 'PRIME B760M-K D4'),
  board('ASUS', 'B760', 'TUF GAMING B760M-PLUS D4'),
  board('ASUS', 'Z790', 'ROG STRIX Z790-I GAMING WIFI'),
  board('ASUS', 'Z790', 'PRIME Z790-A WIFI'),

  board('GIGABYTE', 'B760', 'B760M AORUS ELITE AX'),
  board('GIGABYTE', 'B760', 'B760 AORUS MASTER'),
  board('GIGABYTE', 'Z790', 'Z790 AORUS XTREME X'),
  board('GIGABYTE', 'Z790', 'Z790 AORUS PRO X'),

  board('MSI', 'B760', 'MAG B760M MORTAR WIFI'),
  board('MSI', 'B760', 'PRO B760M-E'),
  board('MSI', 'Z790', 'MEG Z790 GODLIKE'),
  board('MSI', 'Z790', 'MEG Z790 ACE'),

  board('ASRock', 'B760', 'B760M-ITX/D4 WiFi'),
  board('ASRock', 'B760', 'B760 Pro RS WiFi'),
  board('ASRock', 'Z790', 'Z790 Riptide WiFi'),
  board('ASRock', 'Z790', 'Z790M ITX WiFi'),
];
