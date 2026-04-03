import SwiftUI

struct RackCarouselView: View {
    @EnvironmentObject var rackVM: RackViewModel
    @State private var showAddRack = false
    @State private var showDeleteConfirm = false

    var body: some View {
        NavigationStack {
            Group {
                if rackVM.racks.isEmpty {
                    emptyState
                } else {
                    carousel
                }
            }
            .navigationTitle("層架管理")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        showAddRack = true
                    } label: {
                        Image(systemName: "plus")
                    }
                }
                if !rackVM.racks.isEmpty {
                    ToolbarItem(placement: .topBarLeading) {
                        Button(role: .destructive) {
                            showDeleteConfirm = true
                        } label: {
                            Image(systemName: "trash")
                                .foregroundStyle(.red)
                        }
                    }
                }
            }
            .sheet(isPresented: $showAddRack) {
                AddRackView().environmentObject(rackVM)
            }
            .confirmationDialog(
                "刪除層架",
                isPresented: $showDeleteConfirm,
                titleVisibility: .visible
            ) {
                Button("刪除「\(rackVM.racks[safe: rackVM.currentRackIndex]?.name ?? "")」", role: .destructive) {
                    if let rack = rackVM.racks[safe: rackVM.currentRackIndex] {
                        rackVM.deleteRack(id: rack.id)
                    }
                }
                Button("取消", role: .cancel) {}
            } message: {
                Text("此操作無法復原。")
            }
        }
    }

    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "server.rack")
                .font(.system(size: 60))
                .foregroundStyle(.secondary)
            Text("尚無層架")
                .font(.title2)
                .bold()
            Text("點右上角 + 新增第一個層架")
                .foregroundStyle(.secondary)
            Button {
                showAddRack = true
            } label: {
                Label("新增層架", systemImage: "plus")
            }
            .buttonStyle(.borderedProminent)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var carousel: some View {
        VStack(spacing: 0) {
            // Rack counter header
            HStack {
                Text(rackVM.racks[safe: rackVM.currentRackIndex]?.name ?? "")
                    .font(.headline)
                Spacer()
                Text("層架 \(rackVM.currentRackIndex + 1) / \(rackVM.racks.count)")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            .padding(.horizontal)
            .padding(.vertical, 8)

            TabView(selection: $rackVM.currentRackIndex) {
                ForEach(Array(rackVM.racks.enumerated()), id: \.element.id) { index, rack in
                    RackGridView(rack: rack, rackIndex: index + 1)
                        .environmentObject(rackVM)
                        .tag(index)
                }
            }
            .tabViewStyle(.page(indexDisplayMode: .always))
            .indexViewStyle(.page(backgroundDisplayMode: .always))
        }
    }
}

extension Collection {
    subscript(safe index: Index) -> Element? {
        indices.contains(index) ? self[index] : nil
    }
}
