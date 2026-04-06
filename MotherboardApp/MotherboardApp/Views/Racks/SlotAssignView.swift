import SwiftUI

/// Assign a motherboard to a rack slot.
/// Uses the same scraped data as CatalogView via shared CatalogViewModel.
struct SlotAssignView: View {
    let rackID: UUID
    let slotPosition: Int
    let rackIndex: Int
    @EnvironmentObject var rackVM: RackViewModel
    @Environment(\.dismiss) private var dismiss

    @StateObject private var catalogVM = CatalogViewModel()

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Brand picker
                VStack(spacing: 12) {
                    Picker("品牌", selection: $catalogVM.selectedBrand) {
                        Text("選擇品牌").tag("")
                        ForEach(catalogVM.brands, id: \.self) { brand in
                            Text(brand).tag(brand)
                        }
                    }
                    .pickerStyle(.segmented)

                    if !catalogVM.chipsets.isEmpty {
                        Picker("Chipset", selection: $catalogVM.selectedChipset) {
                            Text("全部").tag("")
                            ForEach(catalogVM.chipsets, id: \.self) { chipset in
                                Text(chipset).tag(chipset)
                            }
                        }
                        .pickerStyle(.menu)
                    }
                }
                .padding()
                .onChange(of: catalogVM.selectedBrand) { _, _ in
                    catalogVM.selectedChipset = ""
                }

                Divider()

                if catalogVM.isLoading {
                    ProgressView("載入中...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if catalogVM.filteredModels.isEmpty {
                    Text("請先選擇品牌")
                        .foregroundStyle(.secondary)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List(catalogVM.filteredModels) { board in
                        Button {
                            rackVM.assignModel(board.id, to: slotPosition, in: rackID)
                            dismiss()
                        } label: {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(board.fullModelName)
                                    .font(.headline)
                                    .foregroundStyle(.primary)
                                Text(board.chipset)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle("指定主機板 \(rackIndex)-\(slotPosition)")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") { dismiss() }
                }
            }
            .task { await catalogVM.loadData() }
        }
    }
}
