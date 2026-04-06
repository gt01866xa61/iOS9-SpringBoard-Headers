import Foundation

/// Core data model for a motherboard entry.
/// This is the single source of truth — UI and services only interact with this type.
struct Motherboard: Identifiable, Codable, Hashable {
    /// Unique identifier derived from TPU slug or constructed from brand+model
    let id: String
    /// Manufacturer name: "ASUS", "GIGABYTE", "MSI", "ASRock"
    let brand: String
    /// Chipset: "Z790", "B650", "X570", etc.
    let chipset: String
    /// Full product name — CRITICAL as fallback key for Google search
    let fullModelName: String
    /// URL to the TechPowerUp detail/review page (Stage 1 result)
    let tpuDetailUrl: String?
    /// Resolved official manufacturer support/product URL (Stage 2 result, populated on-demand)
    var officialSupportUrl: String?

    /// Helper: human-readable display combining brand and model
    var displayName: String { "\(brand) \(fullModelName)" }
}
