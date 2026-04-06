import SwiftUI

/// Main catalog view: cascading Pickers (Brand → Chipset) → Model List → Open Safari.
struct CatalogView: View {
    @StateObject private var vm = CatalogViewModel()

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Cascading pickers
                pickerSection

                Divider()

                // Results
                if vm.isLoading {
                    loadingState
                } else if let error = vm.errorMessage {
                    errorState(error)
                } else if vm.filteredModels.isEmpty {
                    emptyState
                } else {
                    modelList
                }
            }
            .navigationTitle("主機板目錄")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        Task { await vm.refreshFromNetwork() }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                    .disabled(vm.isLoading)
                }
            }
            .task { await vm.loadData() }
            .overlay {
                if vm.isResolvingURL {
                    resolvingOverlay
                }
            }
        }
    }

    // MARK: - Picker Section

    private var pickerSection: some View {
        VStack(spacing: 12) {
            Picker("品牌", selection: $vm.selectedBrand) {
                Text("選擇品牌").tag("")
                ForEach(vm.brands, id: \.self) { brand in
                    Text(brand).tag(brand)
                }
            }
            .pickerStyle(.segmented)

            if !vm.chipsets.isEmpty {
                Picker("Chipset", selection: $vm.selectedChipset) {
                    Text("全部 Chipset").tag("")
                    ForEach(vm.chipsets, id: \.self) { chipset in
                        Text(chipset).tag(chipset)
                    }
                }
                .pickerStyle(.menu)
            }
        }
        .padding()
        .onChange(of: vm.selectedBrand) { _, _ in
            vm.selectedChipset = ""
        }
    }

    // MARK: - Model List

    private var modelList: some View {
        List(vm.filteredModels) { board in
            Button {
                Task { await vm.openOfficialPage(for: board) }
            } label: {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(board.fullModelName)
                            .font(.headline)
                            .foregroundStyle(.primary)
                        HStack(spacing: 8) {
                            chipsetBadge(board.chipset)
                            if board.officialSupportUrl != nil {
                                Image(systemName: "checkmark.seal.fill")
                                    .font(.caption)
                                    .foregroundStyle(.green)
                            }
                        }
                    }
                    Spacer()
                    Image(systemName: "safari")
                        .foregroundStyle(.blue)
                }
                .padding(.vertical, 4)
            }
        }
        .listStyle(.plain)
    }

    // MARK: - States

    private var loadingState: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.2)
            Text("正在從 TechPowerUp 載入資料...")
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func errorState(_ message: String) -> some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 40))
                .foregroundStyle(.orange)
            Text("載入失敗")
                .font(.headline)
            Text(message)
                .font(.caption)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
            Button("重試") {
                Task { await vm.refreshFromNetwork() }
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var emptyState: some View {
        VStack(spacing: 12) {
            Image(systemName: "tray")
                .font(.system(size: 40))
                .foregroundStyle(.secondary)
            Text("無符合條件的主機板")
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var resolvingOverlay: some View {
        ZStack {
            Color.black.opacity(0.3).ignoresSafeArea()
            VStack(spacing: 12) {
                ProgressView()
                    .tint(.white)
                Text("正在查詢官網連結...")
                    .foregroundStyle(.white)
                    .font(.subheadline)
            }
            .padding(24)
            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 16))
        }
    }

    // MARK: - Helpers

    private func chipsetBadge(_ chipset: String) -> some View {
        Text(chipset)
            .font(.system(size: 11, weight: .medium))
            .padding(.horizontal, 8)
            .padding(.vertical, 2)
            .background(Color.blue.opacity(0.12))
            .foregroundStyle(.blue)
            .clipShape(Capsule())
    }
}
