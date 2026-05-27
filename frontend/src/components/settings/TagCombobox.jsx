import { useCallback, useEffect, useRef, useState } from "react"
import { createPortal } from "react-dom"
import { Plus, X } from "lucide-react"

import {
  COMPANY_SUGGESTIONS,
  filterLocalSuggestions,
  LOCATION_SUGGESTIONS,
  ROLE_SUGGESTIONS,
  SKILL_SUGGESTIONS,
} from "@/data/searchSuggestions"
import { cn } from "@/lib/utils"
import { apiFetch, parseErrorMessage } from "@/lib/apiClient"

const LOCAL_POOL = {
  roles: ROLE_SUGGESTIONS,
  skills: SKILL_SUGGESTIONS,
  companies: COMPANY_SUGGESTIONS,
  locations: LOCATION_SUGGESTIONS,
}

async function fetchSuggestionsFromApi(kind, query) {
  const path =
    kind === "roles"
      ? `/suggestions/roles?q=${encodeURIComponent(query)}`
      : kind === "companies"
        ? `/suggestions/companies?q=${encodeURIComponent(query)}`
        : kind === "locations"
          ? `/suggestions/locations?q=${encodeURIComponent(query)}`
          : `/suggestions/skills?q=${encodeURIComponent(query)}`
  const res = await apiFetch(path)
  if (!res.ok) {
    const msg = await parseErrorMessage(res)
    throw new Error(msg)
  }
  const data = await res.json()
  return data.suggestions ?? []
}

function mergeSuggestions(apiList, localList, items, limit = 12) {
  const seen = new Set(items.map((i) => i.toLowerCase()))
  const out = []
  for (const s of [...apiList, ...localList]) {
    const key = s.toLowerCase()
    if (!key || seen.has(key)) continue
    seen.add(key)
    out.push(s)
    if (out.length >= limit) break
  }
  return out
}

export function TagCombobox({
  label,
  hint,
  items = [],
  onChange,
  kind = "skills",
  maxItems = 50,
  placeholder = "Search…",
}) {
  const [query, setQuery] = useState("")
  const [suggestions, setSuggestions] = useState([])
  const [open, setOpen] = useState(false)
  const [fetchError, setFetchError] = useState("")
  const [menuStyle, setMenuStyle] = useState(null)
  const wrapRef = useRef(null)
  const menuRef = useRef(null)
  const inputRef = useRef(null)
  const pickingRef = useRef(false)
  const itemsRef = useRef(items)

  useEffect(() => {
    itemsRef.current = items
  }, [items])

  const positionMenu = useCallback(() => {
    const el = inputRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    setMenuStyle({
      position: "fixed",
      top: rect.bottom + 4,
      left: rect.left,
      width: rect.width,
      zIndex: 9999,
    })
  }, [])

  const loadSuggestions = useCallback(
    async (q, itemsOverride = itemsRef.current) => {
      const local = filterLocalSuggestions(LOCAL_POOL[kind] || [], q, itemsOverride, 12)
      const pool = LOCAL_POOL[kind] || []
      if (!pool.length || q.trim().length < 1) {
        setSuggestions(local)
        setFetchError("")
        return local
      }
      if (q.trim().length < 2) {
        setSuggestions(local)
        setFetchError("")
        return local
      }
      try {
        const api = await fetchSuggestionsFromApi(kind, q)
        const merged = mergeSuggestions(api, local, itemsOverride, 12)
        setSuggestions(merged)
        setFetchError("")
        return merged
      } catch {
        setSuggestions(local)
        setFetchError("")
        return local
      }
    },
    [kind]
  )

  const refreshMenu = useCallback(
    async (q = "") => {
      await loadSuggestions(q)
      positionMenu()
      setOpen(true)
    },
    [loadSuggestions, positionMenu]
  )

  useEffect(() => {
    if (!open) return undefined
    let cancelled = false
    const timer = setTimeout(() => {
      loadSuggestions(query).then(() => {
        if (!cancelled) positionMenu()
      })
    }, 120)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [query, loadSuggestions, open, positionMenu])

  useEffect(() => {
    if (!open) return
    void loadSuggestions(query).then(() => positionMenu())
  }, [items, open, query, loadSuggestions, positionMenu])

  useEffect(() => {
    const onDoc = (e) => {
      if (pickingRef.current) return
      const target = e.target
      if (wrapRef.current?.contains(target) || menuRef.current?.contains(target)) {
        return
      }
      setOpen(false)
    }
    document.addEventListener("mousedown", onDoc)
    return () => document.removeEventListener("mousedown", onDoc)
  }, [])

  const addItem = useCallback(
    (value) => {
      const v = String(value).trim()
      const currentItems = itemsRef.current
      if (!v || currentItems.length >= maxItems) return
      const exists = currentItems.some((i) => i.toLowerCase() === v.toLowerCase())
      if (exists) {
        setQuery("")
        void refreshMenu("")
        return
      }
      const nextItems = [...currentItems, v]
      itemsRef.current = nextItems
      onChange(nextItems)
      setQuery("")
      setOpen(true)
      void refreshMenu("")
      requestAnimationFrame(() => inputRef.current?.focus())
    },
    [maxItems, onChange, refreshMenu]
  )

  const removeItem = (value) => onChange(items.filter((i) => i !== value))

  const trimmed = query.trim()
  const canAddCustom =
    trimmed.length >= 1 && !items.some((i) => i.toLowerCase() === trimmed.toLowerCase())

  const onKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault()
      if (canAddCustom) {
        addItem(trimmed)
      } else if (suggestions[0]) {
        addItem(suggestions[0])
      }
    }
    if (e.key === "Escape") setOpen(false)
  }

  const selectSuggestion = (value) => {
    pickingRef.current = true
    addItem(value)
    queueMicrotask(() => {
      pickingRef.current = false
    })
  }

  const showMenu = open && (suggestions.length > 0 || canAddCustom)

  useEffect(() => {
    if (!showMenu) return undefined
    positionMenu()
    const onScroll = () => positionMenu()
    window.addEventListener("scroll", onScroll, true)
    window.addEventListener("resize", onScroll)
    return () => {
      window.removeEventListener("scroll", onScroll, true)
      window.removeEventListener("resize", onScroll)
    }
  }, [showMenu, positionMenu, query, suggestions.length])

  const menu =
    showMenu && menuStyle ? (
      <ul
        ref={menuRef}
        role="listbox"
        style={menuStyle}
        className={cn(
          "max-h-52 overflow-y-auto rounded-lg border border-indigo-500/25 bg-slate-900 py-1 shadow-xl shadow-black/40"
        )}
        onMouseDown={(e) => e.preventDefault()}
      >
        {canAddCustom && (
          <li role="option">
            <button
              type="button"
              className="flex w-full items-center gap-2 border-b border-border px-3 py-2.5 text-left text-sm font-medium text-indigo-300 hover:bg-indigo-500/15"
              onMouseDown={() => selectSuggestion(trimmed)}
            >
              <Plus className="size-4 shrink-0" />
              Add &quot;{trimmed}&quot;
            </button>
          </li>
        )}
        {suggestions.map((s) => (
          <li key={s} role="option">
            <button
              type="button"
              className="flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm hover:bg-indigo-500/15"
              onMouseDown={() => selectSuggestion(s)}
            >
              <Plus className="size-3 shrink-0 text-indigo-400" />
              {s}
            </button>
          </li>
        ))}
      </ul>
    ) : null

  return (
    <div ref={wrapRef} className="relative space-y-2 overflow-visible">
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm font-medium">{label}</p>
        <span className="text-xs text-muted-foreground">
          {items.length}/{maxItems}
        </span>
      </div>
      {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
      {fetchError ? <p className="text-xs text-amber-400">{fetchError}</p> : null}
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <span
            key={item}
            className="inline-flex items-center gap-1 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-2.5 py-0.5 text-xs"
          >
            {item}
            <button
              type="button"
              aria-label={`Remove ${item}`}
              className="rounded-full p-0.5 hover:bg-indigo-500/20"
              onClick={() => removeItem(item)}
            >
              <X className="size-3" />
            </button>
          </span>
        ))}
      </div>
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={query}
          disabled={items.length >= maxItems}
          placeholder={
            items.length >= maxItems
              ? `Max ${maxItems} reached — remove one to add more`
              : placeholder
          }
          className="flex h-10 w-full rounded-lg border border-input bg-background px-3 text-sm"
          onChange={(e) => {
            setQuery(e.target.value)
            if (!open) setOpen(true)
          }}
          onFocus={() => {
            setOpen(true)
            void refreshMenu(query)
          }}
          onKeyDown={onKeyDown}
        />
        {typeof document !== "undefined" && menu ? createPortal(menu, document.body) : null}
      </div>
    </div>
  )
}
