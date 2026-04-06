import Foundation

/// Lightweight cache layer backed by UserDefaults.
/// Stores the Stage-1 motherboard index so we don't scrape on every launch.
final class CacheService {
    static let shared = CacheService()

    private let indexKey = "mb_index_cache_v1"
    private let timestampKey = "mb_index_cache_ts"
    private let cacheLifetime: TimeInterval = 24 * 60 * 60  // 24 hours

    private init() {}

    // MARK: - Index Cache (Stage 1)

    /// Returns cached motherboard list if the cache is still valid, otherwise nil.
    func loadIndex() -> [Motherboard]? {
        guard isCacheValid(),
              let data = UserDefaults.standard.data(forKey: indexKey),
              let boards = try? JSONDecoder().decode([Motherboard].self, from: data)
        else { return nil }
        return boards
    }

    /// Persists the full motherboard index to cache.
    func saveIndex(_ boards: [Motherboard]) {
        if let data = try? JSONEncoder().encode(boards) {
            UserDefaults.standard.set(data, forKey: indexKey)
            UserDefaults.standard.set(Date().timeIntervalSince1970, forKey: timestampKey)
        }
    }

    /// Invalidates the cache, forcing a fresh scrape on next load.
    func invalidate() {
        UserDefaults.standard.removeObject(forKey: indexKey)
        UserDefaults.standard.removeObject(forKey: timestampKey)
    }

    // MARK: - Single-Entry Update (Stage 2)

    /// Updates a single motherboard's `officialSupportUrl` in the cached index.
    func updateOfficialURL(_ url: String, for boardID: String) {
        guard var boards = loadIndex(),
              let idx = boards.firstIndex(where: { $0.id == boardID })
        else { return }
        boards[idx].officialSupportUrl = url
        saveIndex(boards)
    }

    // MARK: - Lookup

    /// Finds a single motherboard by ID in the cache.
    func motherboard(for id: String) -> Motherboard? {
        loadIndex()?.first { $0.id == id }
    }

    // MARK: - Private

    private func isCacheValid() -> Bool {
        let ts = UserDefaults.standard.double(forKey: timestampKey)
        guard ts > 0 else { return false }
        return Date().timeIntervalSince1970 - ts < cacheLifetime
    }
}
