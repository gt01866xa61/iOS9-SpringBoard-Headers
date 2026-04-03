import Foundation

@MainActor
final class CatalogViewModel: ObservableObject {
    @Published var selectedBrand: Brand?
    @Published var selectedChipset: Chipset?

    var allBrands: [Brand] { MotherboardCatalog.brands }

    var availableChipsets: [Chipset] {
        guard let brand = selectedBrand else { return [] }
        return MotherboardCatalog.chipsets(for: brand)
    }

    var availableModels: [MotherboardModel] {
        guard let brand = selectedBrand, let chipset = selectedChipset else { return [] }
        return MotherboardCatalog.models(for: brand, chipset: chipset)
    }

    func selectBrand(_ brand: Brand) {
        selectedBrand = brand
        selectedChipset = nil
    }

    func reset() {
        selectedBrand = nil
        selectedChipset = nil
    }
}
