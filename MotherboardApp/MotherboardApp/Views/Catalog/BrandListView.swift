import SwiftUI

struct BrandListView: View {
    var body: some View {
        List(MotherboardCatalog.brands) { brand in
            NavigationLink(value: brand) {
                HStack(spacing: 12) {
                    Image(systemName: "cpu")
                        .font(.title2)
                        .foregroundStyle(brandColor(for: brand.id))
                        .frame(width: 36)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(brand.displayName)
                            .font(.headline)
                        let count = MotherboardCatalog.models.filter { $0.brandID == brand.id }.count
                        Text("\(count) 個型號")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                .padding(.vertical, 4)
            }
        }
        .navigationTitle("主機板品牌")
        .navigationDestination(for: Brand.self) { brand in
            ChipsetListView(brand: brand)
        }
    }

    private func brandColor(for id: String) -> Color {
        switch id {
        case "asus":     return .blue
        case "gigabyte": return .red
        case "msi":      return .orange
        case "asrock":   return .purple
        default:         return .gray
        }
    }
}
