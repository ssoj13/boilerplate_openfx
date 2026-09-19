#pragma once
// ofxc — shared helpers for every plugin in this series (header-only, links openfx::Support).
//
//  - PixelFormat / dispatchPixelFormat : instantiate one templated processor for the image's
//                                        bit depth x component count, no hand-written switches
//  - toPixel / fromPixel               : normalized <-> storage value conversion
//  - fetchImage                        : fetch + validate a clip image (render scale, field)
//  - runProcessor                      : wire an OFX::ImageProcessor to dst/render window and run it
//  - describeCommon                    : series-wide descriptor defaults
//  - OFXC_REGISTER_PLUGIN              : factory instance + OFX::Plugin::getPluginIDs from CMake metadata

#include "ofxsImageEffect.h"
#include "ofxsProcessing.h"

#include <algorithm>
#include <memory>

namespace ofxc {

// ---- Pixel formats ---------------------------------------------------------

template <class PIX, int nComps, int maxVal>
struct PixelFormat {
    using Pix = PIX;
    static constexpr int nComponents = nComps;
    static constexpr int maxValue = maxVal;  // 1 for float (unclamped), 255 / 65535 for integers
};

/// Normalized value -> storage value. Float passes through; integers are clamped and rounded.
template <class PIX, int maxValue>
inline PIX toPixel(double v)
{
    if constexpr (maxValue == 1)
        return static_cast<PIX>(v);
    else
        return static_cast<PIX>(std::clamp(v, 0.0, 1.0) * maxValue + 0.5);
}

/// Storage value -> normalized value.
template <class PIX, int maxValue>
inline double fromPixel(PIX v)
{
    if constexpr (maxValue == 1)
        return static_cast<double>(v);
    else
        return static_cast<double>(v) / maxValue;
}

inline int componentCount(OFX::PixelComponentEnum comps)
{
    switch (comps) {
    case OFX::ePixelComponentRGBA:  return 4;
    case OFX::ePixelComponentRGB:   return 3;
    case OFX::ePixelComponentAlpha: return 1;
    default:                        return 0;
    }
}

namespace detail {
template <class PIX, int maxValue, class F>
void dispatchComponents(int nComponents, F &&f)
{
    switch (nComponents) {
    case 4: f(PixelFormat<PIX, 4, maxValue>{}); break;
    case 3: f(PixelFormat<PIX, 3, maxValue>{}); break;
    case 1: f(PixelFormat<PIX, 1, maxValue>{}); break;
    default: OFX::throwSuiteStatusException(kOfxStatErrUnsupported);
    }
}
} // namespace detail

/// Calls f(PixelFormat<PIX, nComponents, maxValue>{}) matching the image's depth and components.
/// Use a generic lambda: [&](auto fmt) { using Fmt = decltype(fmt); ... }
template <class F>
void dispatchPixelFormat(const OFX::Image &img, F &&f)
{
    const int n = componentCount(img.getPixelComponents());
    switch (img.getPixelDepth()) {
    case OFX::eBitDepthUByte:  detail::dispatchComponents<unsigned char, 255>(n, f); break;
    case OFX::eBitDepthUShort: detail::dispatchComponents<unsigned short, 65535>(n, f); break;
    case OFX::eBitDepthFloat:  detail::dispatchComponents<float, 1>(n, f); break;
    default: OFX::throwSuiteStatusException(kOfxStatErrUnsupported);
    }
}

// ---- Images & processing ---------------------------------------------------

/// Fetches the clip image for this render and validates it against the render arguments.
/// Returns nullptr only when `optional` is true and the clip is unconnected / has no image.
inline std::unique_ptr<OFX::Image> fetchImage(OFX::Clip *clip, const OFX::RenderArguments &args,
                                              bool optional = false)
{
    if (!clip || (optional && !clip->isConnected()))
        return nullptr;
    std::unique_ptr<OFX::Image> img(clip->fetchImage(args.time));
    if (!img) {
        if (optional)
            return nullptr;
        OFX::throwSuiteStatusException(kOfxStatFailed);
    }
    if (img->getRenderScale().x != args.renderScale.x || img->getRenderScale().y != args.renderScale.y ||
        (img->getField() != OFX::eFieldNone && img->getField() != args.fieldToRender)) {
        OFX::throwSuiteStatusException(kOfxStatFailed);
    }
    return img;
}

/// Runs a CPU processor over args.renderWindow (multi-threaded by the SDK, bounds-checked).
inline void runProcessor(OFX::ImageProcessor &processor, OFX::Image &dst, const OFX::RenderArguments &args)
{
    processor.setDstImg(&dst);
    processor.setRenderWindow(args.renderWindow);
    processor.process();
}

// ---- Descriptors -----------------------------------------------------------

/// Series-wide defaults: labels, grouping, all bit depths, tiles, multi-res, full thread safety.
inline void describeCommon(OFX::ImageEffectDescriptor &desc, const char *label, const char *grouping)
{
    desc.setLabels(label, label, label);
    desc.setPluginGrouping(grouping);
    desc.addSupportedBitDepth(OFX::eBitDepthUByte);
    desc.addSupportedBitDepth(OFX::eBitDepthUShort);
    desc.addSupportedBitDepth(OFX::eBitDepthFloat);
    desc.setSingleInstance(false);
    desc.setHostFrameThreading(false);
    desc.setSupportsMultiResolution(true);
    desc.setSupportsTiles(true);
    desc.setTemporalClipAccess(false);
    desc.setRenderTwiceAlways(false);
    desc.setSupportsMultipleClipPARs(false);
    desc.setRenderThreadSafety(OFX::eRenderFullySafe);
}

} // namespace ofxc

/// Registers FACTORY with the ID/version passed from add_ofx_plugin_bundle() (cmake/OfxPlugin.cmake).
#define OFXC_REGISTER_PLUGIN(FACTORY)                                                   \
    static FACTORY ofxcPluginFactory(PLUGIN_ID, PLUGIN_VERSION_MAJOR, PLUGIN_VERSION_MINOR); \
    namespace OFX { namespace Plugin {                                                  \
    void getPluginIDs(OFX::PluginFactoryArray &ids) { ids.push_back(&ofxcPluginFactory); } \
    } }
