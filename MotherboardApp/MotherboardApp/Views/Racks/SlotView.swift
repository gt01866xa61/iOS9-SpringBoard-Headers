import SwiftUI

struct SlotView: View {
    let slot: RackSlot
    let rackIndex: Int
    let model: Motherboard?
    let onTap: () -> Void

    private var label: String { "\(rackIndex)-\(slot.position)" }

    var body: some View {
        Button(action: onTap) {
            ZStack(alignment: .topTrailing) {
                if let model {
                    filledSlot(model: model)
                } else {
                    emptySlot
                }
                Text(label)
                    .font(.system(size: 9, weight: .bold))
                    .foregroundStyle(.secondary)
                    .padding(3)
            }
        }
        .buttonStyle(.plain)
    }

    private var emptySlot: some View {
        RoundedRectangle(cornerRadius: 8)
            .strokeBorder(Color.secondary.opacity(0.4), style: StrokeStyle(lineWidth: 1.5, dash: [5]))
            .frame(height: 72)
            .overlay {
                Image(systemName: "plus")
                    .foregroundStyle(.tertiary)
                    .font(.title3)
            }
    }

    private func filledSlot(model: Motherboard) -> some View {
        RoundedRectangle(cornerRadius: 8)
            .fill(brandColor(for: model.brand).opacity(0.12))
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .strokeBorder(brandColor(for: model.brand).opacity(0.5), lineWidth: 1)
            )
            .frame(height: 72)
            .overlay {
                VStack(alignment: .leading, spacing: 2) {
                    HStack(spacing: 4) {
                        Text(model.brand)
                            .font(.system(size: 10, weight: .bold))
                            .foregroundStyle(brandColor(for: model.brand))
                        Spacer()
                        Text(model.chipset)
                            .font(.system(size: 9, weight: .medium))
                            .padding(.horizontal, 4)
                            .padding(.vertical, 1)
                            .background(brandColor(for: model.brand).opacity(0.2))
                            .clipShape(Capsule())
                    }
                    Text(model.fullModelName)
                        .font(.system(size: 10))
                        .lineLimit(2)
                        .foregroundStyle(.primary)
                    Spacer()
                }
                .padding(6)
            }
    }

    private func brandColor(for brand: String) -> Color {
        switch brand.uppercased() {
        case "ASUS":     return .blue
        case "GIGABYTE": return .red
        case "MSI":      return .orange
        case "ASROCK":   return .purple
        default:         return .gray
        }
    }
}
