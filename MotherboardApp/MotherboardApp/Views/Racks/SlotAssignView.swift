import SwiftUI

struct SlotAssignView: View {
    let rackID: UUID
    let slotPosition: Int
    let rackIndex: Int
    @EnvironmentObject var rackVM: RackViewModel
    @Environment(\.dismiss) private var dismiss

    @State private var selectedBrand: Brand?
    @State private var selectedChipset: Chipset?

    var body: some View {
        NavigationStack {
            Form {
                Section("品牌") {
                    ForEach(MotherboardCatalog.brands) { brand in
                        HStack {
                            Text(brand.displayName)
                            Spacer()
                            if selectedBrand?.id == brand.id {
                                Image(systemName: "checkmark").foregroundStyle(.blue)
                            }
                        }
                        .contentShape(Rectangle())
                        .onTapGesture {
                            selectedBrand = brand
                            selectedChipset = nil
                        }
                    }
                }

                if let brand = selectedBrand {
                    Section("Chipset") {
                        let chipsets = MotherboardCatalog.chipsets(for: brand)
                        ForEach(chipsets) { chipset in
                            HStack {
                                VStack(alignment: .leading) {
                                    Text(chipset.displayName)
                                    Text(chipset.platform.rawValue)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                Spacer()
                                if selectedChipset?.id == chipset.id {
                                    Image(systemName: "checkmark").foregroundStyle(.blue)
                                }
                            }
                            .contentShape(Rectangle())
                            .onTapGesture { selectedChipset = chipset }
                        }
                    }
                }

                if let brand = selectedBrand, let chipset = selectedChipset {
                    Section("型號") {
                        let models = MotherboardCatalog.models(for: brand, chipset: chipset)
                        ForEach(models) { model in
                            Button {
                                rackVM.assignModel(model.id, to: slotPosition, in: rackID)
                                dismiss()
                            } label: {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(model.name)
                                        .foregroundStyle(.primary)
                                    Text(model.series)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("指定主機板 \(rackIndex)-\(slotPosition)")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") { dismiss() }
                }
            }
        }
    }
}
