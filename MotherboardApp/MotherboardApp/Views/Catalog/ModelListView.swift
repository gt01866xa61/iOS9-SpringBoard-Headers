import SwiftUI

struct ModelListView: View {
    let brand: Brand
    let chipset: Chipset

    private var models: [MotherboardModel] {
        MotherboardCatalog.models(for: brand, chipset: chipset)
    }

    var body: some View {
        List(models) { model in
            VStack(alignment: .leading, spacing: 6) {
                Text(model.name)
                    .font(.headline)
                HStack {
                    Label(model.series, systemImage: "tag")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Spacer()
                    Link(destination: model.productURL) {
                        Label("查看官網", systemImage: "safari")
                            .font(.caption)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 4)
                            .background(Color.blue.opacity(0.1))
                            .foregroundStyle(.blue)
                            .clipShape(Capsule())
                    }
                }
            }
            .padding(.vertical, 4)
        }
        .navigationTitle(chipset.displayName)
        .navigationBarTitleDisplayMode(.large)
    }
}
