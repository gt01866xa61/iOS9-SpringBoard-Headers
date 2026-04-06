import Foundation

/// Drives the Catalog tab UI.
/// Owns the lifecycle: load (cache → scrape) → filter → resolve URL.
@MainActor
final class CatalogViewModel: ObservableObject {

    // MARK: - Published State

    @Published var allMotherboards: [Motherboard] = []
    @Published var selectedBrand: String = ""
    @Published var selectedChipset: String = ""
    @Published var isLoading = false
    @Published var isResolvingURL = false
    @Published var errorMessage: String?

    // MARK: - Derived (Computed)

    var brands: [String] {
        Array(Set(allMotherboards.map(\.brand))).sorted()
    }

    var chipsets: [String] {
        guard !selectedBrand.isEmpty else { return [] }
        return Array(Set(
            allMotherboards
                .filter { $0.brand == selectedBrand }
                .map(\.chipset)
        )).sorted()
    }

    var filteredModels: [Motherboard] {
        allMotherboards.filter { board in
            (selectedBrand.isEmpty || board.brand == selectedBrand) &&
            (selectedChipset.isEmpty || board.chipset == selectedChipset)
        }
    }

    // MARK: - Load Data

    /// Called on appear. Tries cache first, then scrapes.
    func loadData() async {
        guard allMotherboards.isEmpty else { return }

        // 1. Try cache
        if let cached = CacheService.shared.loadIndex() {
            allMotherboards = cached
            if let first = brands.first { selectedBrand = first }
            return
        }

        // 2. Scrape
        await refreshFromNetwork()
    }

    /// Forces a fresh scrape, ignoring cache.
    func refreshFromNetwork() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let boards = try await ScrapingEngine.shared.fetchFullIndex()
            CacheService.shared.saveIndex(boards)
            allMotherboards = boards
            selectedChipset = ""
            if let first = brands.first { selectedBrand = first }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - Resolve & Open URL

    /// Resolves the official URL for a board and opens it in Safari.
    func openOfficialPage(for board: Motherboard) async {
        isResolvingURL = true
        defer { isResolvingURL = false }

        let url = await URLResolverService.resolve(for: board)

        // Update local copy if Stage 2 populated the official URL
        if let idx = allMotherboards.firstIndex(where: { $0.id == board.id }),
           allMotherboards[idx].officialSupportUrl == nil,
           let cached = CacheService.shared.motherboard(for: board.id) {
            allMotherboards[idx].officialSupportUrl = cached.officialSupportUrl
        }

        await MainActor.run {
            UIApplication.shared.open(url)
        }
    }

    // MARK: - Selection Helpers

    func selectBrand(_ brand: String) {
        selectedBrand = brand
        selectedChipset = ""
    }
}
