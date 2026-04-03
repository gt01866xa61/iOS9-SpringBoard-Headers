import SwiftUI

struct ChipsetListView: View {
    let brand: Brand

    private var chipsetsByPlatform: [(Platform, [Chipset])] {
        let chipsets = MotherboardCatalog.chipsets(for: brand)
        let grouped = Dictionary(grouping: chipsets, by: { $0.platform })
        return Platform.allCases.compactMap { platform in
            guard let items = grouped[platform], !items.isEmpty else { return nil }
            return (platform, items)
        }
    }

    var body: some View {
        List {
            ForEach(chipsetsByPlatform, id: \.0) { platform, chipsets in
                Section(platform.rawValue) {
                    ForEach(chipsets) { chipset in
                        NavigationLink(value: ChipsetSelection(brand: brand, chipset: chipset)) {
                            HStack {
                                Text(chipset.displayName)
                                    .font(.headline)
                                Spacer()
                                let count = MotherboardCatalog.models(for: brand, chipset: chipset).count
                                Text("\(count) 個型號")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            .padding(.vertical, 2)
                        }
                    }
                }
            }
        }
        .navigationTitle(brand.displayName)
        .navigationDestination(for: ChipsetSelection.self) { selection in
            ModelListView(brand: selection.brand, chipset: selection.chipset)
        }
    }
}

struct ChipsetSelection: Hashable {
    let brand: Brand
    let chipset: Chipset
}
