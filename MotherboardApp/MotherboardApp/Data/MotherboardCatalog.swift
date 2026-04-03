import Foundation

enum MotherboardCatalog {

    // MARK: - Brands

    static let brands: [Brand] = [
        Brand(id: "asus",     displayName: "ASUS",     shortName: "ASUS"),
        Brand(id: "gigabyte", displayName: "GIGABYTE",  shortName: "GB"),
        Brand(id: "msi",      displayName: "MSI",       shortName: "MSI"),
        Brand(id: "asrock",   displayName: "ASRock",    shortName: "ASR"),
    ]

    // MARK: - Chipsets

    static let chipsets: [Chipset] = [
        // Intel LGA1700
        Chipset(id: "z790",  displayName: "Z790",  platform: .intelLGA1700),
        Chipset(id: "b760",  displayName: "B760",  platform: .intelLGA1700),
        Chipset(id: "h770",  displayName: "H770",  platform: .intelLGA1700),
        Chipset(id: "z690",  displayName: "Z690",  platform: .intelLGA1700),
        Chipset(id: "b660",  displayName: "B660",  platform: .intelLGA1700),
        // AMD AM5
        Chipset(id: "x670e", displayName: "X670E", platform: .amdAM5),
        Chipset(id: "x670",  displayName: "X670",  platform: .amdAM5),
        Chipset(id: "b650e", displayName: "B650E", platform: .amdAM5),
        Chipset(id: "b650",  displayName: "B650",  platform: .amdAM5),
        // AMD AM4
        Chipset(id: "x570",  displayName: "X570",  platform: .amdAM4),
        Chipset(id: "b550",  displayName: "B550",  platform: .amdAM4),
    ]

    // MARK: - Models

    static let models: [MotherboardModel] = asusModels + gigabyteModels + msiModels + asrockModels

    // MARK: ASUS

    private static let asusModels: [MotherboardModel] = [
        // Z790
        MotherboardModel(id: "asus-rog-maximus-z790-hero",
                         name: "ROG MAXIMUS Z790 HERO",
                         brandID: "asus", chipsetID: "z790", series: "ROG",
                         productURL: URL(string: "https://www.asus.com/motherboards-components/motherboards/rog/rog-maximus-z790-hero/")!),
        MotherboardModel(id: "asus-rog-strix-z790-e",
                         name: "ROG STRIX Z790-E GAMING WIFI",
                         brandID: "asus", chipsetID: "z790", series: "ROG",
                         productURL: URL(string: "https://www.asus.com/motherboards-components/motherboards/rog/rog-strix-z790-e-gaming-wifi/")!),
        MotherboardModel(id: "asus-tuf-z790-plus-wifi",
                         name: "TUF GAMING Z790-PLUS WIFI",
                         brandID: "asus", chipsetID: "z790", series: "TUF Gaming",
                         productURL: URL(string: "https://www.asus.com/motherboards-components/motherboards/tuf-gaming/tuf-gaming-z790-plus-wifi/")!),
        MotherboardModel(id: "asus-prime-z790-p-wifi",
                         name: "PRIME Z790-P WIFI",
                         brandID: "asus", chipsetID: "z790", series: "PRIME",
                         productURL: URL(string: "https://www.asus.com/motherboards-components/motherboards/prime/prime-z790-p-wifi/")!),
        // B760
        MotherboardModel(id: "asus-tuf-b760m-plus-wifi",
                         name: "TUF GAMING B760M-PLUS WIFI",
                         brandID: "asus", chipsetID: "b760", series: "TUF Gaming",
                         productURL: URL(string: "https://www.asus.com/motherboards-components/motherboards/tuf-gaming/tuf-gaming-b760m-plus-wifi/")!),
        MotherboardModel(id: "asus-prime-b760m-a-wifi",
                         name: "PRIME B760M-A WIFI",
                         brandID: "asus", chipsetID: "b760", series: "PRIME",
                         productURL: URL(string: "https://www.asus.com/motherboards-components/motherboards/prime/prime-b760m-a-wifi/")!),
        MotherboardModel(id: "asus-rog-strix-b760-g",
                         name: "ROG STRIX B760-G GAMING WIFI",
                         brandID: "asus", chipsetID: "b760", series: "ROG",
                         productURL: URL(string: "https://www.asus.com/motherboards-components/motherboards/rog/rog-strix-b760-g-gaming-wifi/")!),
        // Z690
        MotherboardModel(id: "asus-rog-maximus-z690-hero",
                         name: "ROG MAXIMUS Z690 HERO",
                         brandID: "asus", chipsetID: "z690", series: "ROG",
                         productURL: URL(string: "https://www.asus.com/motherboards-components/motherboards/rog/rog-maximus-z690-hero/")!),
        MotherboardModel(id: "asus-tuf-z690-plus-wifi",
                         name: "TUF GAMING Z690-PLUS WIFI D4",
                         brandID: "asus", chipsetID: "z690", series: "TUF Gaming",
                         productURL: URL(string: "https://www.asus.com/motherboards-components/motherboards/tuf-gaming/tuf-gaming-z690-plus-wifi-d4/")!),
        // B660
        MotherboardModel(id: "asus-prime-b660m-a-wifi",
                         name: "PRIME B660M-A WIFI D4",
                         brandID: "asus", chipsetID: "b660", series: "PRIME",
                         productURL: URL(string: "https://www.asus.com/motherboards-components/motherboards/prime/prime-b660m-a-wifi-d4/")!),
        // X670E
        MotherboardModel(id: "asus-rog-crosshair-x670e-hero",
                         name: "ROG CROSSHAIR X670E HERO",
                         brandID: "asus", chipsetID: "x670e", series: "ROG",
                         productURL: URL(string: "https://www.asus.com/motherboards-components/motherboards/rog/rog-crosshair-x670e-hero/")!),
        MotherboardModel(id: "asus-rog-strix-x670e-e",
                         name: "ROG STRIX X670E-E GAMING WIFI",
                         brandID: "asus", chipsetID: "x670e", series: "ROG",
                         productURL: URL(string: "https://www.asus.com/motherboards-components/motherboards/rog/rog-strix-x670e-e-gaming-wifi/")!),
        MotherboardModel(id: "asus-tuf-x670e-plus-wifi",
                         name: "TUF GAMING X670E-PLUS WIFI",
                         brandID: "asus", chipsetID: "x670e", series: "TUF Gaming",
                         productURL: URL(string: "https://www.asus.com/motherboards-components/motherboards/tuf-gaming/tuf-gaming-x670e-plus-wifi/")!),
        // B650
        MotherboardModel(id: "asus-tuf-b650-plus-wifi",
                         name: "TUF GAMING B650-PLUS WIFI",
                         brandID: "asus", chipsetID: "b650", series: "TUF Gaming",
                         productURL: URL(string: "https://www.asus.com/motherboards-components/motherboards/tuf-gaming/tuf-gaming-b650-plus-wifi/")!),
        MotherboardModel(id: "asus-prime-b650m-a-wifi",
                         name: "PRIME B650M-A WIFI",
                         brandID: "asus", chipsetID: "b650", series: "PRIME",
                         productURL: URL(string: "https://www.asus.com/motherboards-components/motherboards/prime/prime-b650m-a-wifi/")!),
        // X570
        MotherboardModel(id: "asus-rog-crosshair-viii-dark-hero",
                         name: "ROG CROSSHAIR VIII DARK HERO",
                         brandID: "asus", chipsetID: "x570", series: "ROG",
                         productURL: URL(string: "https://www.asus.com/motherboards-components/motherboards/rog/rog-crosshair-viii-dark-hero/")!),
        MotherboardModel(id: "asus-tuf-x570-plus-wifi",
                         name: "TUF GAMING X570-PLUS (WI-FI)",
                         brandID: "asus", chipsetID: "x570", series: "TUF Gaming",
                         productURL: URL(string: "https://www.asus.com/motherboards-components/motherboards/tuf-gaming/tuf-gaming-x570-plus-wi-fi/")!),
        // B550
        MotherboardModel(id: "asus-rog-strix-b550-f",
                         name: "ROG STRIX B550-F GAMING (WI-FI II)",
                         brandID: "asus", chipsetID: "b550", series: "ROG",
                         productURL: URL(string: "https://www.asus.com/motherboards-components/motherboards/rog/rog-strix-b550-f-gaming-wi-fi-ii/")!),
    ]

    // MARK: GIGABYTE

    private static let gigabyteModels: [MotherboardModel] = [
        // Z790
        MotherboardModel(id: "gb-z790-aorus-master",
                         name: "Z790 AORUS MASTER",
                         brandID: "gigabyte", chipsetID: "z790", series: "AORUS",
                         productURL: URL(string: "https://www.gigabyte.com/Motherboard/Z790-AORUS-MASTER-rev-10")!),
        MotherboardModel(id: "gb-z790-aorus-elite-ax",
                         name: "Z790 AORUS ELITE AX",
                         brandID: "gigabyte", chipsetID: "z790", series: "AORUS",
                         productURL: URL(string: "https://www.gigabyte.com/Motherboard/Z790-AORUS-ELITE-AX-rev-10")!),
        MotherboardModel(id: "gb-z790-gaming-x-ax",
                         name: "Z790 GAMING X AX",
                         brandID: "gigabyte", chipsetID: "z790", series: "Gaming",
                         productURL: URL(string: "https://www.gigabyte.com/Motherboard/Z790-GAMING-X-AX-rev-10")!),
        // B760
        MotherboardModel(id: "gb-b760m-aorus-elite-ax",
                         name: "B760M AORUS ELITE AX",
                         brandID: "gigabyte", chipsetID: "b760", series: "AORUS",
                         productURL: URL(string: "https://www.gigabyte.com/Motherboard/B760M-AORUS-ELITE-AX-rev-10")!),
        MotherboardModel(id: "gb-b760-ds3h-ax",
                         name: "B760 DS3H AX",
                         brandID: "gigabyte", chipsetID: "b760", series: "UD",
                         productURL: URL(string: "https://www.gigabyte.com/Motherboard/B760-DS3H-AX-rev-10")!),
        // X670E
        MotherboardModel(id: "gb-x670e-aorus-master",
                         name: "X670E AORUS MASTER",
                         brandID: "gigabyte", chipsetID: "x670e", series: "AORUS",
                         productURL: URL(string: "https://www.gigabyte.com/Motherboard/X670E-AORUS-MASTER-rev-10")!),
        MotherboardModel(id: "gb-x670e-aorus-elite-ax",
                         name: "X670E AORUS ELITE AX",
                         brandID: "gigabyte", chipsetID: "x670e", series: "AORUS",
                         productURL: URL(string: "https://www.gigabyte.com/Motherboard/X670E-AORUS-ELITE-AX-rev-10")!),
        // B650
        MotherboardModel(id: "gb-b650-aorus-elite-ax",
                         name: "B650 AORUS ELITE AX",
                         brandID: "gigabyte", chipsetID: "b650", series: "AORUS",
                         productURL: URL(string: "https://www.gigabyte.com/Motherboard/B650-AORUS-ELITE-AX-rev-10")!),
        MotherboardModel(id: "gb-b650m-aorus-pro-ax",
                         name: "B650M AORUS PRO AX",
                         brandID: "gigabyte", chipsetID: "b650", series: "AORUS",
                         productURL: URL(string: "https://www.gigabyte.com/Motherboard/B650M-AORUS-PRO-AX-rev-10")!),
        // X570
        MotherboardModel(id: "gb-x570-aorus-master",
                         name: "X570 AORUS MASTER",
                         brandID: "gigabyte", chipsetID: "x570", series: "AORUS",
                         productURL: URL(string: "https://www.gigabyte.com/Motherboard/X570-AORUS-MASTER-rev-11")!),
        MotherboardModel(id: "gb-x570-gaming-x",
                         name: "X570 GAMING X",
                         brandID: "gigabyte", chipsetID: "x570", series: "Gaming",
                         productURL: URL(string: "https://www.gigabyte.com/Motherboard/X570-GAMING-X-rev-10")!),
        // B550
        MotherboardModel(id: "gb-b550-aorus-pro-ax",
                         name: "B550 AORUS PRO AX",
                         brandID: "gigabyte", chipsetID: "b550", series: "AORUS",
                         productURL: URL(string: "https://www.gigabyte.com/Motherboard/B550-AORUS-PRO-AX-rev-10")!),
    ]

    // MARK: MSI

    private static let msiModels: [MotherboardModel] = [
        // Z790
        MotherboardModel(id: "msi-meg-z790-ace",
                         name: "MEG Z790 ACE",
                         brandID: "msi", chipsetID: "z790", series: "MEG",
                         productURL: URL(string: "https://www.msi.com/Motherboard/MEG-Z790-ACE")!),
        MotherboardModel(id: "msi-mpg-z790-carbon-wifi",
                         name: "MPG Z790 CARBON WIFI",
                         brandID: "msi", chipsetID: "z790", series: "MPG",
                         productURL: URL(string: "https://www.msi.com/Motherboard/MPG-Z790-CARBON-WIFI")!),
        MotherboardModel(id: "msi-mag-z790-tomahawk-wifi",
                         name: "MAG Z790 TOMAHAWK WIFI",
                         brandID: "msi", chipsetID: "z790", series: "MAG",
                         productURL: URL(string: "https://www.msi.com/Motherboard/MAG-Z790-TOMAHAWK-WIFI")!),
        MotherboardModel(id: "msi-pro-z790-a-wifi",
                         name: "PRO Z790-A WIFI",
                         brandID: "msi", chipsetID: "z790", series: "PRO",
                         productURL: URL(string: "https://www.msi.com/Motherboard/PRO-Z790-A-WIFI")!),
        // B760
        MotherboardModel(id: "msi-mag-b760-tomahawk-wifi",
                         name: "MAG B760 TOMAHAWK WIFI",
                         brandID: "msi", chipsetID: "b760", series: "MAG",
                         productURL: URL(string: "https://www.msi.com/Motherboard/MAG-B760-TOMAHAWK-WIFI")!),
        MotherboardModel(id: "msi-pro-b760m-a-wifi",
                         name: "PRO B760M-A WIFI",
                         brandID: "msi", chipsetID: "b760", series: "PRO",
                         productURL: URL(string: "https://www.msi.com/Motherboard/PRO-B760M-A-WIFI")!),
        // X670E
        MotherboardModel(id: "msi-meg-x670e-ace",
                         name: "MEG X670E ACE",
                         brandID: "msi", chipsetID: "x670e", series: "MEG",
                         productURL: URL(string: "https://www.msi.com/Motherboard/MEG-X670E-ACE")!),
        MotherboardModel(id: "msi-mpg-x670e-carbon-wifi",
                         name: "MPG X670E CARBON WIFI",
                         brandID: "msi", chipsetID: "x670e", series: "MPG",
                         productURL: URL(string: "https://www.msi.com/Motherboard/MPG-X670E-CARBON-WIFI")!),
        // B650
        MotherboardModel(id: "msi-mag-b650-tomahawk-wifi",
                         name: "MAG B650 TOMAHAWK WIFI",
                         brandID: "msi", chipsetID: "b650", series: "MAG",
                         productURL: URL(string: "https://www.msi.com/Motherboard/MAG-B650-TOMAHAWK-WIFI")!),
        MotherboardModel(id: "msi-pro-b650-s-wifi",
                         name: "PRO B650-S WIFI",
                         brandID: "msi", chipsetID: "b650", series: "PRO",
                         productURL: URL(string: "https://www.msi.com/Motherboard/PRO-B650-S-WIFI")!),
        // X570
        MotherboardModel(id: "msi-meg-x570-godlike",
                         name: "MEG X570 GODLIKE",
                         brandID: "msi", chipsetID: "x570", series: "MEG",
                         productURL: URL(string: "https://www.msi.com/Motherboard/MEG-X570-GODLIKE")!),
        MotherboardModel(id: "msi-mpg-x570-gaming-edge-wifi",
                         name: "MPG X570 GAMING EDGE WIFI",
                         brandID: "msi", chipsetID: "x570", series: "MPG",
                         productURL: URL(string: "https://www.msi.com/Motherboard/MPG-X570-GAMING-EDGE-WIFI")!),
        // B550
        MotherboardModel(id: "msi-mag-b550-tomahawk",
                         name: "MAG B550 TOMAHAWK",
                         brandID: "msi", chipsetID: "b550", series: "MAG",
                         productURL: URL(string: "https://www.msi.com/Motherboard/MAG-B550-TOMAHAWK")!),
    ]

    // MARK: ASRock

    private static let asrockModels: [MotherboardModel] = [
        // Z790
        MotherboardModel(id: "asrock-z790-taichi",
                         name: "Z790 Taichi",
                         brandID: "asrock", chipsetID: "z790", series: "Taichi",
                         productURL: URL(string: "https://www.asrock.com/mb/Intel/Z790%20Taichi/")!),
        MotherboardModel(id: "asrock-z790-pg-lightning",
                         name: "Z790 PG Lightning",
                         brandID: "asrock", chipsetID: "z790", series: "Phantom Gaming",
                         productURL: URL(string: "https://www.asrock.com/mb/Intel/Z790%20PG%20Lightning/")!),
        MotherboardModel(id: "asrock-z790-pro-rs",
                         name: "Z790 Pro RS",
                         brandID: "asrock", chipsetID: "z790", series: "Pro",
                         productURL: URL(string: "https://www.asrock.com/mb/Intel/Z790%20Pro%20RS/")!),
        // B760
        MotherboardModel(id: "asrock-b760m-pg-riptide",
                         name: "B760M PG Riptide",
                         brandID: "asrock", chipsetID: "b760", series: "Phantom Gaming",
                         productURL: URL(string: "https://www.asrock.com/mb/Intel/B760M%20PG%20Riptide/")!),
        MotherboardModel(id: "asrock-b760-pro-rs",
                         name: "B760 Pro RS",
                         brandID: "asrock", chipsetID: "b760", series: "Pro",
                         productURL: URL(string: "https://www.asrock.com/mb/Intel/B760%20Pro%20RS/")!),
        // X670E
        MotherboardModel(id: "asrock-x670e-taichi",
                         name: "X670E Taichi",
                         brandID: "asrock", chipsetID: "x670e", series: "Taichi",
                         productURL: URL(string: "https://www.asrock.com/mb/AMD/X670E%20Taichi/")!),
        MotherboardModel(id: "asrock-x670e-pg-lightning",
                         name: "X670E PG Lightning",
                         brandID: "asrock", chipsetID: "x670e", series: "Phantom Gaming",
                         productURL: URL(string: "https://www.asrock.com/mb/AMD/X670E%20PG%20Lightning/")!),
        // B650
        MotherboardModel(id: "asrock-b650-pg-lightning",
                         name: "B650 PG Lightning",
                         brandID: "asrock", chipsetID: "b650", series: "Phantom Gaming",
                         productURL: URL(string: "https://www.asrock.com/mb/AMD/B650%20PG%20Lightning/")!),
        MotherboardModel(id: "asrock-b650m-pro-rs",
                         name: "B650M Pro RS",
                         brandID: "asrock", chipsetID: "b650", series: "Pro",
                         productURL: URL(string: "https://www.asrock.com/mb/AMD/B650M%20Pro%20RS/")!),
        // X570
        MotherboardModel(id: "asrock-x570-taichi",
                         name: "X570 Taichi",
                         brandID: "asrock", chipsetID: "x570", series: "Taichi",
                         productURL: URL(string: "https://www.asrock.com/mb/AMD/X570%20Taichi/")!),
        MotherboardModel(id: "asrock-x570-pg-velocita",
                         name: "X570 Phantom Gaming Velocita",
                         brandID: "asrock", chipsetID: "x570", series: "Phantom Gaming",
                         productURL: URL(string: "https://www.asrock.com/mb/AMD/X570%20Phantom%20Gaming%20Velocita/")!),
        // B550
        MotherboardModel(id: "asrock-b550-taichi",
                         name: "B550 Taichi",
                         brandID: "asrock", chipsetID: "b550", series: "Taichi",
                         productURL: URL(string: "https://www.asrock.com/mb/AMD/B550%20Taichi/")!),
    ]

    // MARK: - Query Helpers

    static func brand(for id: String) -> Brand? {
        brands.first { $0.id == id }
    }

    static func chipset(for id: String) -> Chipset? {
        chipsets.first { $0.id == id }
    }

    static func model(for id: String) -> MotherboardModel? {
        models.first { $0.id == id }
    }

    static func chipsets(for brand: Brand) -> [Chipset] {
        let chipsetIDs = Set(models.filter { $0.brandID == brand.id }.map { $0.chipsetID })
        return chipsets.filter { chipsetIDs.contains($0.id) }
    }

    static func models(for brand: Brand, chipset: Chipset) -> [MotherboardModel] {
        models.filter { $0.brandID == brand.id && $0.chipsetID == chipset.id }
    }
}
