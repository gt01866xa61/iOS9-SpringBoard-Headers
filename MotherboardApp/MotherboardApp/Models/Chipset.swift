import Foundation

enum Platform: String, CaseIterable, Codable {
    case intelLGA1700 = "Intel LGA1700"
    case intelLGA1200 = "Intel LGA1200"
    case amdAM5 = "AMD AM5"
    case amdAM4 = "AMD AM4"
}

struct Chipset: Identifiable, Hashable {
    let id: String
    let displayName: String
    let platform: Platform
}
